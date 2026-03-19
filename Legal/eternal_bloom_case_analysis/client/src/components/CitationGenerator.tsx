import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Copy, Check, Download, BookOpen } from 'lucide-react';
import { toast } from 'sonner';

export interface Citation {
  id: string;
  name: string;
  type: 'statute' | 'rule' | 'case' | 'constitutional' | 'regulation';
  year?: number;
  court?: string;
  section?: string;
  subsection?: string;
}

interface CitationFormats {
  bluebook: string;
  alwd: string;
  apa: string;
}

type CitationFormat = 'bluebook' | 'alwd' | 'apa';

const generateCitations = (citation: Citation): CitationFormats => {
  const { name, type, year, court, section, subsection } = citation;

  // Helper function to format section symbols
  const formatSection = (sec?: string, subsec?: string) => {
    if (!sec) return '';
    const symbol = '§';
    if (subsec) return `${symbol} ${sec}(${subsec})`;
    return `${symbol} ${sec}`;
  };

  // Bluebook format (19th edition)
  let bluebook = '';
  switch (type) {
    case 'statute':
      bluebook = `${name} ${formatSection(section, subsection)}`;
      if (year) bluebook += ` (${year})`;
      break;
    case 'rule':
      bluebook = `${name} ${formatSection(section, subsection)}`;
      break;
    case 'constitutional':
      bluebook = `U.S. CONST. ${formatSection(section, subsection)}`;
      break;
    case 'regulation':
      bluebook = `${formatSection(section, subsection)} (${name})`;
      if (year) bluebook += ` (${year})`;
      break;
    case 'case':
      bluebook = `${name}`;
      if (year) bluebook += ` (${year})`;
      if (court) bluebook += ` (${court})`;
      break;
    default:
      bluebook = name;
  }

  // ALWD format (6th edition)
  let alwd = '';
  switch (type) {
    case 'statute':
      alwd = `${name} § ${section}`;
      if (subsection) alwd += `(${subsection})`;
      if (year) alwd += ` (${year})`;
      break;
    case 'rule':
      alwd = `${name} Rule ${section}`;
      if (subsection) alwd += `(${subsection})`;
      break;
    case 'constitutional':
      alwd = `U.S. Const. art. ${section}`;
      if (subsection) alwd += `, § ${subsection}`;
      break;
    case 'regulation':
      alwd = `${section} C.F.R. § ${subsection || section} (${name})`;
      if (year) alwd += ` (${year})`;
      break;
    case 'case':
      alwd = `${name}`;
      if (year) alwd += ` (${year})`;
      if (court) alwd += ` (${court})`;
      break;
    default:
      alwd = name;
  }

  // APA format (7th edition)
  let apa = '';
  switch (type) {
    case 'statute':
      apa = `${name}, ${section}`;
      if (subsection) apa += `(${subsection})`;
      if (year) apa += ` (${year})`;
      break;
    case 'rule':
      apa = `${name}, Rule ${section}`;
      if (subsection) apa += `(${subsection})`;
      break;
    case 'constitutional':
      apa = `U.S. Constitution, Article ${section}`;
      if (subsection) apa += `, Section ${subsection}`;
      break;
    case 'regulation':
      apa = `${section} C.F.R. § ${subsection || section}`;
      if (year) apa += ` (${name}, ${year})`;
      break;
    case 'case':
      apa = `${name}`;
      if (year) apa += ` (${year})`;
      if (court) apa += ` (${court})`;
      break;
    default:
      apa = name;
  }

  return { bluebook, alwd, apa };
};

interface CitationGeneratorProps {
  citations?: Citation[];
  onCitationSelect?: (citation: Citation) => void;
}

export function CitationGenerator({ citations = [], onCitationSelect }: CitationGeneratorProps) {
  const [selectedCitations, setSelectedCitations] = useState<Citation[]>([]);
  const [copiedFormat, setCopiedFormat] = useState<CitationFormat | null>(null);
  const [activeFormat, setActiveFormat] = useState<CitationFormat>('bluebook');

  // Default citations if none provided
  const defaultCitations: Citation[] = [
    {
      id: 'mcl-554-139',
      name: 'Michigan Compiled Laws',
      type: 'statute',
      section: '554.139',
      year: 2024,
    },
    {
      id: 'mcl-600-2919a',
      name: 'Michigan Compiled Laws',
      type: 'statute',
      section: '600.2919a',
      year: 2024,
    },
    {
      id: 'mcl-125-2301',
      name: 'Mobile Home Commission Act',
      type: 'statute',
      section: '125.2301',
      year: 2024,
    },
    {
      id: 'mcr-2-105',
      name: 'Michigan Court Rules',
      type: 'rule',
      section: '2.105',
    },
    {
      id: 'mcr-2-107',
      name: 'Michigan Court Rules',
      type: 'rule',
      section: '2.107',
    },
    {
      id: 'us-const-14',
      name: 'United States Constitution',
      type: 'constitutional',
      section: 'XIV',
      subsection: '1',
    },
    {
      id: '42-usc-1983',
      name: '42 U.S.C.',
      type: 'statute',
      section: '1983',
      year: 2024,
    },
    {
      id: 'egle-part-31',
      name: 'EGLE Environmental Protection Act',
      type: 'regulation',
      section: 'Part 31',
      year: 2024,
    },
  ];

  const citationsToUse = citations.length > 0 ? citations : defaultCitations;

  const toggleCitation = (citation: Citation) => {
    setSelectedCitations((prev) =>
      prev.some((c) => c.id === citation.id)
        ? prev.filter((c) => c.id !== citation.id)
        : [...prev, citation]
    );
    onCitationSelect?.(citation);
  };

  const copyToClipboard = (text: string, format: CitationFormat) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedFormat(format);
      toast.success(`${format.toUpperCase()} citation copied!`);
      setTimeout(() => setCopiedFormat(null), 2000);
    });
  };

  const generateBibliography = (format: CitationFormat) => {
    if (selectedCitations.length === 0) {
      toast.error('Please select at least one citation');
      return;
    }

    const citations = selectedCitations
      .map((c) => {
        const formats = generateCitations(c);
        return formats[format];
      })
      .join('\n\n');

    copyToClipboard(citations, format);
  };

  const downloadCitations = () => {
    if (selectedCitations.length === 0) {
      toast.error('Please select at least one citation');
      return;
    }

    const bluebookCitations = selectedCitations
      .map((c) => generateCitations(c).bluebook)
      .join('\n\n');

    const element = document.createElement('a');
    element.setAttribute(
      'href',
      `data:text/plain;charset=utf-8,${encodeURIComponent(bluebookCitations)}`
    );
    element.setAttribute('download', 'legal_citations.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast.success('Citations downloaded!');
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-accent" />
          Legal Citation Generator
        </CardTitle>
        <CardDescription>
          Generate properly formatted citations in Bluebook, ALWD, or APA format
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Citation Selection */}
        <div>
          <h3 className="text-sm font-semibold text-foreground mb-3">Select Authorities to Cite</h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
            {citationsToUse.map((citation) => (
              <button
                key={citation.id}
                onClick={() => toggleCitation(citation)}
                className={`p-3 rounded-lg border text-left transition-all ${
                  selectedCitations.some((c) => c.id === citation.id)
                    ? 'border-accent bg-accent/10'
                    : 'border-border hover:border-accent/50 hover:bg-secondary/30'
                }`}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex-1">
                    <p className="font-medium text-foreground text-sm">{citation.name}</p>
                    {citation.section && (
                      <p className="text-xs text-muted-foreground mt-1">§ {citation.section}</p>
                    )}
                  </div>
                  <Badge variant="outline" className="text-xs whitespace-nowrap">
                    {citation.type}
                  </Badge>
                </div>
              </button>
            ))}
          </div>
        </div>

        {/* Citation Format Tabs */}
        {selectedCitations.length > 0 && (
          <div>
            <h3 className="text-sm font-semibold text-foreground mb-3">Generated Citations</h3>
            <Tabs value={activeFormat} onValueChange={(v) => setActiveFormat(v as CitationFormat)}>
              <TabsList className="grid w-full grid-cols-3">
                <TabsTrigger value="bluebook">Bluebook</TabsTrigger>
                <TabsTrigger value="alwd">ALWD</TabsTrigger>
                <TabsTrigger value="apa">APA</TabsTrigger>
              </TabsList>

              {(['bluebook', 'alwd', 'apa'] as const).map((format) => (
                <TabsContent key={format} value={format} className="space-y-3">
                  <div className="space-y-3">
                    {selectedCitations.map((citation) => {
                      const formats = generateCitations(citation);
                      const citationText = formats[format];

                      return (
                        <div
                          key={citation.id}
                          className="p-4 rounded-lg border border-border bg-secondary/20 space-y-2"
                        >
                          <p className="text-sm font-medium text-foreground">{citation.name}</p>
                          <div className="flex items-start gap-2">
                            <code className="flex-1 text-xs bg-background p-2 rounded border border-border text-foreground overflow-x-auto">
                              {citationText}
                            </code>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => copyToClipboard(citationText, format)}
                              className="flex-shrink-0"
                            >
                              {copiedFormat === format ? (
                                <Check className="w-4 h-4" />
                              ) : (
                                <Copy className="w-4 h-4" />
                              )}
                            </Button>
                          </div>
                        </div>
                      );
                    })}
                  </div>

                  {/* Copy All Button */}
                  <Button
                    onClick={() => generateBibliography(format)}
                    className="w-full"
                    variant="default"
                  >
                    <Copy className="w-4 h-4 mr-2" />
                    Copy All {format.toUpperCase()} Citations
                  </Button>
                </TabsContent>
              ))}
            </Tabs>
          </div>
        )}

        {/* Action Buttons */}
        {selectedCitations.length > 0 && (
          <div className="flex gap-2">
            <Button onClick={downloadCitations} variant="outline" className="flex-1">
              <Download className="w-4 h-4 mr-2" />
              Download as Text
            </Button>
            <Button
              onClick={() => setSelectedCitations([])}
              variant="outline"
              className="flex-1"
            >
              Clear Selection
            </Button>
          </div>
        )}

        {/* Info Box */}
        <div className="p-4 bg-secondary/30 rounded-lg border border-border space-y-2">
          <p className="text-sm font-semibold text-foreground">Citation Format Guide</p>
          <ul className="space-y-1 text-xs text-muted-foreground">
            <li>
              <strong>Bluebook:</strong> Standard for law review articles and legal documents
            </li>
            <li>
              <strong>ALWD:</strong> Association of Legal Writing Directors format
            </li>
            <li>
              <strong>APA:</strong> American Psychological Association format for academic papers
            </li>
          </ul>
        </div>

        {/* Selection Summary */}
        {selectedCitations.length > 0 && (
          <div className="p-3 bg-accent/10 rounded-lg border border-accent/20">
            <p className="text-sm text-foreground">
              <strong>{selectedCitations.length}</strong> citation{selectedCitations.length !== 1 ? 's' : ''} selected
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
