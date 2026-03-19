#!/usr/bin/env python3
"""
REUSABLE CHRONOLOGICAL TIMELINE PDF GENERATOR
LitigationOS — Skills Module

Generates court-ready demonstrative exhibit timeline PDFs from structured event
data. Parameterized for any case, any court, any parties.

Usage:
    # Programmatic — supply your own events
    from skills.timeline_generator import generate_timeline_pdf

    events = [
        {
            'date': '2024-01-15', 'actor': 'Plaintiff',
            'title': 'Filed Motion', 'description': 'Motion for summary disposition',
            'case_type': 'CUSTODY', 'event_type': 'filing',
            'harm': 'Delayed proceedings', 'authority': 'MCR 2.116',
            'relief': 'Grant motion',
        },
    ]
    generate_timeline_pdf(
        case_name='Pigors v. Watson',
        case_numbers=['2024-001507-DC', '2023-5907-PP'],
        court_name='14th Circuit Court, Muskegon County, Michigan',
        plaintiff='Andrew J. Pigors',
        defendant='Tiffany Watson',
        output_path='timeline.pdf',
        events=events,
    )

    # From database — auto-query master_chronological_timeline
    from skills.timeline_generator import generate_from_db

    generate_from_db(
        db_path='litigation_context.db',
        case_type_filter='HOUSING',
        output_path='housing_timeline.pdf',
        case_name='Pigors v. Shady Oaks',
        court_name='60th District Court, Muskegon',
        plaintiff='Andrew J. Pigors',
        defendant='Shady Oaks Park MHP, LLC',
    )
"""

import sqlite3
import os
from datetime import datetime, date
from collections import defaultdict

try:
    from fpdf import FPDF
except ImportError:
    raise ImportError("fpdf2 is required: pip install fpdf2")


# ── Latin-1 sanitizer (fpdf core fonts only support latin-1) ──

_UNICODE_REPLACEMENTS = {
    '\u2014': '--', '\u2013': '-', '\u2019': "'", '\u2018': "'",
    '\u201c': '"', '\u201d': '"', '\u2026': '...', '\u2022': '*',
    '\u2605': '[*]', '\u2b50': '[*]', '\u26a0': '[!]', '\u26d3': '[chain]',
    '\U0001f507': '[muted]', '\U0001f4cb': '[doc]', '\u2696': '[scales]',
    '\xad': '-', '\u200b': '', '\u00a0': ' ', '\ufeff': '',
    '\u2610': '[ ]', '\u2611': '[x]', '\u2612': '[x]',
    '\ud83d': '', '\ud83c': '', '\udfe0': '', '\u2764': '[heart]',
    '\u26a1': '[!]', '\u2728': '*', '\u274c': '[X]',
    '\u2705': '[OK]', '\u2757': '[!]', '\U0001f6a8': '[!]',
    '\U0001f525': '[!]', '\U0001f4a5': '[!]', '\U0001f50d': '[search]',
    '\U0001f4dd': '[note]', '\U0001f4c4': '[doc]', '\U0001f4c5': '[cal]',
    '\U0001f9d1': '[person]', '\U0001f46e': '[officer]',
    '\U0001f3e0': '[house]', '\U0001f6d1': '[stop]',
    '\u2660': '*', '\u2663': '*', '\u2665': '*', '\u2666': '*',
    '\U0001f9f1': '', '\U0001f4b0': '', '\U0001f46a': '',
}


def safe(text):
    """Sanitize text for latin-1 encoding (fpdf core font requirement)."""
    if text is None:
        return ''
    s = str(text)
    for old, new in _UNICODE_REPLACEMENTS.items():
        s = s.replace(old, new)
    s = s.encode('latin-1', errors='replace').decode('latin-1')
    return s.strip()


# ── Default color palette ──

DEFAULT_COLORS = {
    'red':       (180, 30, 30),
    'blue':      (30, 60, 150),
    'gold':      (180, 130, 0),
    'green':     (30, 120, 50),
    'purple':    (100, 30, 130),
    'orange':    (200, 80, 0),
    'gray':      (100, 100, 100),
    'black':     (0, 0, 0),
    'white':     (255, 255, 255),
    'bg_light':  (245, 245, 245),
    'bg_narrative': (255, 248, 230),
    'header_bg': (20, 40, 80),
    'month_bg':  (230, 235, 245),
}


def _resolve_actor_color(actor, event_type, actor_color_map, palette):
    """Resolve an actor string to an RGB color tuple.

    Args:
        actor: Actor name from the event.
        event_type: Event type string (e.g. 'ex_parte').
        actor_color_map: Dict mapping actor substring (lowercase) to a color
            key name (str referencing ``palette``) or an RGB tuple directly.
        palette: The full color palette dict.

    Returns:
        RGB tuple (r, g, b).
    """
    if event_type == 'ex_parte':
        return palette.get('orange', (200, 80, 0))
    actor_lower = (actor or '').lower()
    for key, color_val in actor_color_map.items():
        if key.lower() in actor_lower:
            if isinstance(color_val, str):
                return palette.get(color_val, palette.get('gray', (100, 100, 100)))
            return color_val
    return palette.get('gray', (100, 100, 100))


def _get_event_symbol(event_type, title='', description=''):
    """Return a short text symbol for the event type."""
    txt = ((title or '') + ' ' + (description or '')).lower()
    if 'ex parte' in txt or event_type == 'ex_parte':
        return '[!EP]'
    if 'contempt' in txt or 'jail' in txt:
        return '[CONT]'
    if 'mute' in txt or 'muted' in txt or 'silenc' in txt:
        return '[MUTED]'
    if event_type == 'hearing':
        return '[HEAR]'
    if event_type == 'filing':
        return '[FILE]'
    if event_type == 'order':
        return '[ORD]'
    if 'critical' in txt:
        return '[**]'
    return ''


# ── PDF class ──

class _TimelinePDF(FPDF):
    """Internal PDF subclass for timeline generation."""

    def __init__(self, case_name, plaintiff, disclaimer_text):
        super().__init__(orientation='P', unit='mm', format='Letter')
        self.set_auto_page_break(auto=True, margin=20)
        self._case_name = case_name
        self._plaintiff = plaintiff
        self._disclaimer = disclaimer_text
        self._palette = dict(DEFAULT_COLORS)

    def header(self):
        if self.page_no() <= 2:
            return
        self.set_font('Helvetica', 'B', 8)
        self.set_text_color(*self._palette['gray'])
        self.cell(0, 5, safe('%s | Chronological Timeline | Page %d' % (
            self._case_name, self.page_no())), align='C')
        self.ln(3)
        self.set_draw_color(*self._palette['gray'])
        self.line(15, self.get_y(), self.w - 15, self.get_y())
        self.ln(3)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 7)
        self.set_text_color(*self._palette['gray'])
        self.cell(0, 5, safe('%s  |  Page %d' % (self._disclaimer, self.page_no())), align='C')

    def colored_cell(self, w, h, txt, color, bold=False, align='L', fill=False, fill_color=None):
        self.set_text_color(*color)
        style = 'B' if bold else ''
        if fill and fill_color:
            self.set_fill_color(*fill_color)
        self.set_font('Helvetica', style, self.font_size_pt)
        self.cell(w, h, safe(txt), align=align, fill=fill)

    def section_box(self, title, body, border_color, bg_color=None):
        """Draw a bordered narrative box with title bar."""
        if bg_color is None:
            bg_color = self._palette['bg_narrative']
        if self.get_y() > self.h - 60:
            self.add_page()
        self.set_draw_color(*border_color)
        self.set_line_width(0.6)
        self.set_fill_color(*border_color)
        self.set_font('Helvetica', 'B', 10)
        self.set_text_color(*self._palette['white'])
        self.cell(self.w - 30, 7, safe('  ' + title), fill=True, align='L')
        self.ln(7)
        self.set_fill_color(*bg_color)
        self.set_font('Helvetica', '', 8.5)
        self.set_text_color(*self._palette['black'])
        self.multi_cell(self.w - 30, 4.5, safe(body), fill=True)
        self.ln(3)
        self.set_line_width(0.2)


# ── Page builders ──

def _build_title_page(pdf, case_name, case_numbers, court_name, plaintiff,
                      defendant, disclaimer_text, palette):
    """Build the cover / title page."""
    pdf.add_page()
    pdf.ln(30)
    pdf.set_font('Helvetica', 'B', 24)
    pdf.set_text_color(*palette['header_bg'])
    pdf.cell(0, 12, safe('COMPREHENSIVE'), align='C')
    pdf.ln(12)
    pdf.cell(0, 12, safe('CHRONOLOGICAL TIMELINE'), align='C')
    pdf.ln(18)
    pdf.set_draw_color(*palette['gold'])
    pdf.set_line_width(1)
    pdf.line(50, pdf.get_y(), pdf.w - 50, pdf.get_y())
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 13)
    pdf.set_text_color(*palette['black'])
    pdf.cell(0, 8, safe(case_name), align='C')
    pdf.ln(8)
    pdf.set_font('Helvetica', '', 11)
    pdf.cell(0, 7, safe(court_name), align='C')
    pdf.ln(12)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*palette['header_bg'])
    for cn in case_numbers:
        pdf.cell(0, 6, safe('Case No. %s' % cn), align='C')
        pdf.ln(6)
    pdf.ln(9)
    pdf.set_draw_color(*palette['gold'])
    pdf.line(50, pdf.get_y(), pdf.w - 50, pdf.get_y())
    pdf.ln(12)
    pdf.set_font('Helvetica', '', 11)
    pdf.set_text_color(*palette['black'])
    pdf.cell(0, 7, safe('Prepared by %s' % plaintiff), align='C')
    pdf.ln(7)
    pdf.cell(0, 7, safe('Pro Se Plaintiff / Appellant'), align='C')
    pdf.ln(12)
    pdf.set_font('Helvetica', 'I', 10)
    pdf.cell(0, 6, safe('Date Prepared: %s' % datetime.now().strftime('%B %d, %Y')), align='C')
    pdf.ln(15)
    # Disclaimer box
    pdf.set_draw_color(*palette['red'])
    pdf.set_line_width(0.5)
    x = 40
    w = pdf.w - 80
    y = pdf.get_y()
    pdf.rect(x, y, w, 14)
    pdf.set_xy(x + 2, y + 2)
    pdf.set_font('Helvetica', 'B', 10)
    pdf.set_text_color(*palette['red'])
    pdf.cell(w - 4, 5, safe(disclaimer_text), align='C')
    pdf.set_xy(x + 2, y + 7)
    pdf.set_font('Helvetica', '', 8)
    pdf.cell(w - 4, 5, safe('This timeline is prepared for illustrative purposes to assist the Court.'), align='C')


def _build_legend_page(pdf, actor_color_map, legend_items, parties, palette,
                       case_descriptions=None):
    """Build the legend / key page.

    Args:
        pdf: The _TimelinePDF instance.
        actor_color_map: Dict of actor->color used for the color legend.
        legend_items: List of (rgb_tuple, label_str, description_str) for color legend.
            If None, auto-generated from actor_color_map.
        parties: List of (name, description) tuples for key parties section.
        palette: Color palette dict.
        case_descriptions: Optional list of (short_label, full_description) for
            the case structure section.
    """
    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*palette['header_bg'])
    pdf.cell(0, 10, safe('LEGEND / KEY'), align='C')
    pdf.ln(12)

    # Color coding
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*palette['black'])
    pdf.cell(0, 7, safe('COLOR CODING BY ACTOR / EVENT TYPE:'))
    pdf.ln(8)

    if legend_items is None:
        legend_items = []
        for actor_key, color_val in actor_color_map.items():
            if isinstance(color_val, str):
                rgb = palette.get(color_val, palette['gray'])
            else:
                rgb = color_val
            legend_items.append((rgb, actor_key.upper(), actor_key.title()))

    for color, label, desc in legend_items:
        pdf.set_fill_color(*color)
        pdf.rect(20, pdf.get_y() + 1, 8, 4, 'F')
        pdf.set_x(32)
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*color)
        pdf.cell(25, 6, safe(label))
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*palette['black'])
        pdf.cell(0, 6, safe('= ' + desc))
        pdf.ln(6.5)

    pdf.ln(6)

    # Symbols
    pdf.set_font('Helvetica', 'B', 11)
    pdf.set_text_color(*palette['black'])
    pdf.cell(0, 7, safe('EVENT SYMBOLS:'))
    pdf.ln(8)
    symbols = [
        ('[**]',    'CRITICAL -- Event of high significance'),
        ('[!EP]',   'EX PARTE -- Order entered without notice/hearing'),
        ('[CONT]',  'CONTEMPT / JAIL -- Contempt sanction or incarceration'),
        ('[MUTED]', 'MUTED -- Party silenced/muted during hearing'),
        ('[FILE]',  'FILING -- Motion, complaint, or document filed'),
        ('[HEAR]',  'HEARING -- Court hearing or proceeding'),
        ('[ORD]',   'ORDER -- Court order entered'),
    ]
    for sym, desc in symbols:
        pdf.set_font('Helvetica', 'B', 9)
        pdf.set_text_color(*palette.get('orange', (200, 80, 0)) if 'EP' in sym else palette['header_bg'])
        pdf.cell(18, 6, safe(sym))
        pdf.set_font('Helvetica', '', 9)
        pdf.set_text_color(*palette['black'])
        pdf.cell(0, 6, safe(desc))
        pdf.ln(6)

    # Case structure
    if case_descriptions:
        pdf.ln(6)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*palette['black'])
        pdf.cell(0, 7, safe('CASE STRUCTURE:'))
        pdf.ln(8)
        for short_label, full_desc in case_descriptions:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(*palette['header_bg'])
            pdf.cell(40, 6, safe(short_label))
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*palette['black'])
            pdf.cell(0, 6, safe(full_desc))
            pdf.ln(6)

    # Key parties
    if parties:
        pdf.ln(6)
        pdf.set_font('Helvetica', 'B', 11)
        pdf.set_text_color(*palette['black'])
        pdf.cell(0, 7, safe('KEY PARTIES:'))
        pdf.ln(8)
        for name, desc in parties:
            pdf.set_font('Helvetica', 'B', 9)
            pdf.set_text_color(*palette['header_bg'])
            pdf.cell(45, 5.5, safe(name))
            pdf.set_font('Helvetica', '', 9)
            pdf.set_text_color(*palette['black'])
            pdf.cell(0, 5.5, safe('-- ' + desc))
            pdf.ln(5.5)


def _build_timeline_pages(pdf, events, narratives, actor_color_map, palette,
                          date_range_label=None):
    """Build the chronological timeline event pages.

    Args:
        pdf: The _TimelinePDF instance.
        events: List of event dicts with keys: date, actor, title, description,
            case_type, event_type, harm, authority, relief.
        narratives: Dict mapping month key 'YYYY-MM' to narrative dict with
            keys: title, color (RGB tuple), body.
        actor_color_map: Dict for color resolution.
        palette: Color palette dict.
        date_range_label: Optional string like 'May 2025 through January 2026'.

    Returns:
        Number of events printed.
    """
    month_names = {
        1: 'January', 2: 'February', 3: 'March', 4: 'April',
        5: 'May', 6: 'June', 7: 'July', 8: 'August',
        9: 'September', 10: 'October', 11: 'November', 12: 'December'
    }

    # Group by month
    by_month = defaultdict(list)
    for ev in events:
        month_key = ev['date'][:7]
        by_month[month_key].append(ev)

    # Determine month range from data
    if by_month:
        all_months = sorted(by_month.keys())
        start_ym = all_months[0].split('-')
        end_ym = all_months[-1].split('-')
        start_y, start_m = int(start_ym[0]), int(start_ym[1])
        end_y, end_m = int(end_ym[0]), int(end_ym[1])
    else:
        start_y, start_m = datetime.now().year, 1
        end_y, end_m = datetime.now().year, 12

    months = []
    y, m = start_y, start_m
    while (y, m) <= (end_y, end_m):
        months.append('%04d-%02d' % (y, m))
        m += 1
        if m > 12:
            m = 1
            y += 1

    if date_range_label is None:
        date_range_label = '%s %d through %s %d' % (
            month_names[start_m], start_y, month_names[end_m], end_y)

    pdf.add_page()
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*palette['header_bg'])
    pdf.cell(0, 10, safe('CHRONOLOGICAL TIMELINE OF EVENTS'), align='C')
    pdf.ln(10)
    pdf.set_font('Helvetica', '', 9)
    pdf.set_text_color(*palette['gray'])
    pdf.cell(0, 5, safe(date_range_label), align='C')
    pdf.ln(8)

    events_printed = 0

    for month_key in months:
        month_events = by_month.get(month_key, [])
        y_val = int(month_key[:4])
        m_val = int(month_key[5:7])
        month_label = '%s %d' % (month_names[m_val], y_val)

        if pdf.get_y() > pdf.h - 40:
            pdf.add_page()

        # Month header bar
        pdf.set_fill_color(*palette['month_bg'])
        pdf.set_draw_color(*palette['header_bg'])
        pdf.set_line_width(0.3)
        y_pos = pdf.get_y()
        pdf.rect(15, y_pos, pdf.w - 30, 7, 'FD')
        pdf.set_xy(17, y_pos)
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_text_color(*palette['header_bg'])
        count_str = '(%d events)' % len(month_events) if month_events else '(no key events)'
        pdf.cell(pdf.w - 34, 7, safe('%s    %s' % (month_label, count_str)))
        pdf.set_y(y_pos + 8)

        if not month_events:
            pdf.set_font('Helvetica', 'I', 8)
            pdf.set_text_color(*palette['gray'])
            pdf.cell(0, 5, safe('    No significant events this month.'))
            pdf.ln(6)
        else:
            for ev in month_events:
                if pdf.get_y() > pdf.h - 25:
                    pdf.add_page()

                color = _resolve_actor_color(ev.get('actor', ''),
                                             ev.get('event_type', ''),
                                             actor_color_map, palette)
                symbol = _get_event_symbol(ev.get('event_type', ''),
                                           ev.get('title', ''),
                                           ev.get('description', ''))
                title_str = ev.get('title', '')
                desc_str = ev.get('description', '')
                is_critical = (ev.get('event_type') == 'ex_parte' or
                               'critical' in title_str.lower() or
                               'jail' in title_str.lower() or
                               'suspend' in title_str.lower())

                # Date column
                pdf.set_font('Helvetica', 'B' if is_critical else '', 8)
                pdf.set_text_color(*palette['black'])
                pdf.cell(22, 5, safe(ev.get('date', '')))

                # Symbol
                if symbol:
                    pdf.set_font('Helvetica', 'B', 7)
                    pdf.set_text_color(*palette.get('orange', (200, 80, 0)) if 'EP' in symbol else color)
                    pdf.cell(14, 5, safe(symbol))
                else:
                    pdf.cell(14, 5, '')

                # Actor
                pdf.set_font('Helvetica', 'B', 8)
                pdf.set_text_color(*color)
                pdf.cell(32, 5, safe((ev.get('actor', '') or '')[:18]))

                # Case type tag
                case_tag = ''
                ct = ev.get('case_type', '')
                if ct:
                    case_tag = '[%s]' % ct[:6]
                pdf.set_font('Helvetica', '', 7)
                pdf.set_text_color(*palette['gray'])
                pdf.cell(14, 5, safe(case_tag))

                # Title
                remaining = pdf.w - 15 - 22 - 14 - 32 - 14
                pdf.set_font('Helvetica', 'B' if is_critical else '', 8)
                pdf.set_text_color(*color)
                pdf.cell(remaining, 5, safe(title_str[:80]),
                         new_x='LMARGIN', new_y='NEXT')

                # Description
                if desc_str and desc_str != title_str and len(desc_str) > 10:
                    pdf.set_x(82)
                    pdf.set_font('Helvetica', '', 7)
                    pdf.set_text_color(*palette['gray'])
                    pdf.multi_cell(pdf.w - 97, 3.8, safe(desc_str[:200]))

                # Authority violated
                auth = ev.get('authority', '')
                if auth:
                    pdf.set_x(82)
                    pdf.set_font('Helvetica', 'I', 7)
                    pdf.set_text_color(*palette['red'])
                    pdf.cell(0, 3.8, safe('Authority violated: %s' % auth[:100]))
                    pdf.ln(4)

                # Relief sought
                relief = ev.get('relief', '')
                if relief:
                    pdf.set_x(82)
                    pdf.set_font('Helvetica', 'I', 7)
                    pdf.set_text_color(*palette['green'])
                    pdf.cell(0, 3.8, safe('Relief: %s' % relief[:100]))
                    pdf.ln(4)

                pdf.ln(1.5)
                events_printed += 1

        # Insert narrative after specific months
        if month_key in (narratives or {}):
            pdf.ln(2)
            n = narratives[month_key]
            n_color = n.get('color', palette['red'])
            pdf.section_box(n['title'], n['body'], n_color)
            pdf.ln(2)

    return events_printed


def _build_summary_page(pdf, stats, key_finding_text, palette, footnote_text=None):
    """Build the summary statistics page.

    Args:
        pdf: The _TimelinePDF instance.
        stats: List of (label, value, color_rgb) tuples for stat rows.
        key_finding_text: Text body for the key finding box.
        palette: Color palette dict.
        footnote_text: Optional footnote at bottom of page.
    """
    pdf.add_page()
    pdf.ln(5)
    pdf.set_font('Helvetica', 'B', 16)
    pdf.set_text_color(*palette['header_bg'])
    pdf.cell(0, 10, safe('SUMMARY STATISTICS'), align='C')
    pdf.ln(12)
    pdf.set_draw_color(*palette['gold'])
    pdf.set_line_width(0.8)
    pdf.line(40, pdf.get_y(), pdf.w - 40, pdf.get_y())
    pdf.ln(8)

    for label, value, color in stats:
        pdf.set_font('Helvetica', '', 10)
        pdf.set_text_color(*palette['black'])
        pdf.cell(110, 8, safe(label))
        pdf.set_font('Helvetica', 'B', 12)
        pdf.set_text_color(*color)
        pdf.cell(0, 8, safe(str(value)), align='R')
        pdf.ln(8)
        pdf.set_draw_color(*palette['bg_light'])
        pdf.line(25, pdf.get_y(), pdf.w - 25, pdf.get_y())
        pdf.ln(1)

    if key_finding_text:
        pdf.ln(8)
        pdf.section_box('KEY FINDING', key_finding_text, palette['red'])

    if footnote_text:
        pdf.ln(5)
        pdf.set_font('Helvetica', 'I', 8)
        pdf.set_text_color(*palette['gray'])
        pdf.multi_cell(0, 4, safe(footnote_text))


# ═══════════════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════════════

def generate_timeline_pdf(
    case_name,
    case_numbers,
    court_name,
    plaintiff,
    defendant,
    output_path,
    events,
    narratives=None,
    summary_stats=None,
    key_finding_text=None,
    footnote_text=None,
    color_map=None,
    legend_items=None,
    parties=None,
    case_descriptions=None,
    date_range_label=None,
    disclaimer_text=None,
    palette_overrides=None,
):
    """Generate a court-ready chronological timeline PDF.

    Args:
        case_name: Display name (e.g. 'Pigors v. Watson').
        case_numbers: List of case number strings.
        court_name: Full court name string.
        plaintiff: Plaintiff name string.
        defendant: Defendant name string.
        output_path: File path for the output PDF.
        events: List of event dicts. Required keys: 'date', 'actor', 'title'.
            Optional keys: 'description', 'case_type', 'event_type', 'harm',
            'authority', 'relief'.
        narratives: Optional dict mapping 'YYYY-MM' to narrative dicts with
            keys: 'title', 'body', 'color' (RGB tuple).
        summary_stats: Optional list of (label, value, color_rgb) tuples.
        key_finding_text: Optional text for the key finding box on summary page.
        footnote_text: Optional footnote for the summary page.
        color_map: Dict mapping actor substrings (lowercase) to palette key
            strings or RGB tuples. E.g. {'shady oaks': 'blue', 'andrew': 'green'}.
        legend_items: Optional list of (rgb_tuple, label, description) for
            the legend page. Auto-generated from color_map if None.
        parties: Optional list of (name, description) for key parties section.
        case_descriptions: Optional list of (short_label, full_desc) for case
            structure on the legend page.
        date_range_label: Optional override for the date range header text.
        disclaimer_text: Override the default disclaimer. Default:
            'DEMONSTRATIVE EXHIBIT -- NOT FILED AS EVIDENCE'.
        palette_overrides: Dict of color overrides merged into DEFAULT_COLORS.

    Returns:
        Dict with keys: 'output_path', 'pages', 'events_printed', 'file_size_kb'.
    """
    if disclaimer_text is None:
        disclaimer_text = 'DEMONSTRATIVE EXHIBIT -- NOT FILED AS EVIDENCE'

    palette = dict(DEFAULT_COLORS)
    if palette_overrides:
        palette.update(palette_overrides)

    if color_map is None:
        color_map = {}

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    pdf = _TimelinePDF(case_name, plaintiff, disclaimer_text)
    pdf._palette = palette

    # Title page
    _build_title_page(pdf, case_name, case_numbers, court_name, plaintiff,
                      defendant, disclaimer_text, palette)

    # Legend page
    _build_legend_page(pdf, color_map, legend_items, parties or [], palette,
                       case_descriptions)

    # Timeline pages
    events_printed = _build_timeline_pages(
        pdf, events, narratives or {}, color_map, palette, date_range_label)

    # Summary page (if stats provided)
    if summary_stats or key_finding_text:
        _build_summary_page(pdf, summary_stats or [], key_finding_text,
                            palette, footnote_text)

    pdf.output(output_path)

    page_count = pdf.page_no()
    file_size = os.path.getsize(output_path)

    return {
        'output_path': output_path,
        'pages': page_count,
        'events_printed': events_printed,
        'file_size_kb': round(file_size / 1024, 1),
    }


def generate_from_db(
    db_path,
    case_type_filter,
    output_path,
    case_name=None,
    case_numbers=None,
    court_name=None,
    plaintiff=None,
    defendant=None,
    color_map=None,
    legend_items=None,
    parties=None,
    case_descriptions=None,
    narratives=None,
    key_finding_text=None,
    summary_stats=None,
    footnote_text=None,
    disclaimer_text=None,
    limit=500,
    actor_filter=None,
    deduplicate=True,
):
    """Query master_chronological_timeline and generate a timeline PDF.

    Convenience wrapper that queries the database directly, deduplicates
    events, and calls ``generate_timeline_pdf``.

    Args:
        db_path: Path to the SQLite database.
        case_type_filter: Value to match against ``case_type`` column
            (e.g. 'HOUSING', 'CUSTODY', 'PPO').
        output_path: Output PDF file path.
        case_name: Case display name. Defaults to 'Timeline — <case_type_filter>'.
        case_numbers: List of case number strings. Defaults to empty.
        court_name: Court name string. Defaults to generic.
        plaintiff: Plaintiff name. Defaults to 'Plaintiff'.
        defendant: Defendant name. Defaults to 'Defendant'.
        color_map: Actor color map (see generate_timeline_pdf).
        legend_items: Legend items (see generate_timeline_pdf).
        parties: Key parties list.
        case_descriptions: Case structure descriptions.
        narratives: Narrative boxes dict.
        key_finding_text: Key finding box text.
        summary_stats: Summary stats list.
        footnote_text: Footnote text.
        disclaimer_text: Disclaimer override.
        limit: Max events to query. Default 500.
        actor_filter: Optional list of actor names to include. If None, all.
        deduplicate: If True, dedup by (date, actor, event_type). Default True.

    Returns:
        Dict with generation results (same as generate_timeline_pdf).
    """
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    query = """
        SELECT id, event_date, case_type, event_type, actor, title, description,
               harm_to_andrew, authority_violated
        FROM master_chronological_timeline
        WHERE case_type = ?
    """
    params = [case_type_filter]

    if actor_filter:
        placeholders = ','.join(['?'] * len(actor_filter))
        query += ' AND actor IN (%s)' % placeholders
        params.extend(actor_filter)

    query += ' ORDER BY event_date, actor LIMIT ?'
    params.append(limit)

    cur.execute(query, params)
    raw = cur.fetchall()
    conn.close()

    # Deduplicate
    if deduplicate and raw:
        grouped = defaultdict(list)
        for row in raw:
            key = (row[1], row[4], row[3])  # date, actor, event_type
            grouped[key].append(row)

        deduped = []
        for key, group in grouped.items():
            def _title_quality(r):
                t = r[5] or ''
                if len(t) > 120:
                    return -len(t)
                return 100 - len(t)
            best = max(group, key=_title_quality)
            deduped.append(best)
        deduped.sort(key=lambda r: (r[1], r[4]))
        raw = deduped

    events = []
    for row in raw:
        eid, edate, ctype, etype, actor, title, desc, harm, auth = row
        events.append({
            'date': edate or '',
            'actor': actor or '',
            'title': (title or '')[:120].strip(),
            'description': (desc or '')[:250].strip(),
            'case_type': ctype or '',
            'event_type': etype or '',
            'harm': harm or '',
            'authority': auth or '',
            'relief': '',
        })

    if case_name is None:
        case_name = 'Timeline -- %s' % case_type_filter
    if case_numbers is None:
        case_numbers = []
    if court_name is None:
        court_name = 'Michigan Circuit Court'
    if plaintiff is None:
        plaintiff = 'Plaintiff'
    if defendant is None:
        defendant = 'Defendant'

    return generate_timeline_pdf(
        case_name=case_name,
        case_numbers=case_numbers,
        court_name=court_name,
        plaintiff=plaintiff,
        defendant=defendant,
        output_path=output_path,
        events=events,
        narratives=narratives,
        summary_stats=summary_stats,
        key_finding_text=key_finding_text,
        footnote_text=footnote_text,
        color_map=color_map,
        legend_items=legend_items,
        parties=parties,
        case_descriptions=case_descriptions,
        disclaimer_text=disclaimer_text,
    )


# ── CLI entry point ──

if __name__ == '__main__':
    import sys

    if len(sys.argv) < 4:
        print('Usage: python timeline_generator.py <db_path> <case_type> <output.pdf>')
        print('Example: python timeline_generator.py litigation_context.db HOUSING housing_timeline.pdf')
        sys.exit(1)

    db_path = sys.argv[1]
    case_type = sys.argv[2]
    out_path = sys.argv[3]

    print('Generating %s timeline from %s ...' % (case_type, db_path))
    result = generate_from_db(db_path=db_path, case_type_filter=case_type,
                              output_path=out_path)
    print('Done: %d events, %d pages, %.1f KB -> %s' % (
        result['events_printed'], result['pages'],
        result['file_size_kb'], result['output_path']))
