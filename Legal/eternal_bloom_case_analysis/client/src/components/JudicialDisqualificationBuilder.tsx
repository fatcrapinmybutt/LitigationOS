import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { AlertTriangle, Copy, Download, FileText, Scale, CheckCircle2 } from 'lucide-react';
import { toast } from 'sonner';

interface BiasPattern {
  id: string;
  title: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM';
  legalBasis: string[];
  description: string;
  evidence: string[];
  impact: string;
}

interface MotionSection {
  id: string;
  title: string;
  content: string;
  required: boolean;
}

const biasPatterns: BiasPattern[] = [
  {
    id: 'pattern-1',
    title: 'Ex Parte Orders Without Affidavits or Findings of Fact',
    severity: 'CRITICAL',
    legalBasis: ['MCR 3.206(A)', 'MCL 722.27(1)(c)', '14th Amendment Due Process'],
    description: 'Judge McNeill issued parenting time suspension orders via telephone without requiring affidavits, written findings of fact, or documented emergency circumstances.',
    evidence: [
      'Parenting time suspension ordered via phone call (June 15, 2024)',
      'No affidavit filed supporting emergency circumstances',
      'No written findings of fact explaining the suspension',
      'Subsequent orders referencing HealthWest evaluation without formal submission'
    ],
    impact: 'Plaintiff denied opportunity to present evidence or respond to allegations before parenting time suspension'
  },
  {
    id: 'pattern-2',
    title: 'Denial of Parenting Time Modification Due to Sanction Fee Barrier',
    severity: 'CRITICAL',
    legalBasis: ['MCR 3.203', 'Due Process (Access to Courts)', 'MCL 722.27(1)(c)'],
    description: 'Judge McNeill imposed a $250 sanction fee as a barrier to filing parenting time modification motions, effectively denying plaintiff\'s constitutional right to petition the court.',
    evidence: [
      'Modification motion denied due to unpaid $250 sanction fee',
      'Fee described as barrier to future filings',
      'Plaintiff unable to modify parenting time due to fee constraint',
      'Employment loss directly linked to inability to modify parenting time'
    ],
    impact: 'Plaintiff effectively barred from exercising statutory modification rights; employment consequences resulted from court-imposed constraints'
  },
  {
    id: 'pattern-3',
    title: 'Delayed Hearings and Notice Failures',
    severity: 'HIGH',
    legalBasis: ['MCR 3.203', 'MCL 722.27', 'Due Process (Notice)'],
    description: 'Judge McNeill consistently delayed hearings on parenting time matters beyond reasonable timeframes and failed to provide adequate notice of hearing dates and modifications.',
    evidence: [
      'Modification motions filed without timely hearing scheduling',
      'Delays exceeding 30 days in custody/parenting time matters',
      'Notice of hearing modifications provided without sufficient advance notice',
      'Parenting time changes implemented without proper notice to plaintiff'
    ],
    impact: 'Plaintiff unable to prepare adequate response; parenting time disrupted without notice; employment and childcare arrangements destabilized'
  },
  {
    id: 'pattern-4',
    title: 'Misrepresentation of Income and Selective Fact-Finding',
    severity: 'HIGH',
    legalBasis: ['MCR 2.313 (Judicial Conduct)', 'MCL 722.27(1)(c)', 'Due Process'],
    description: 'Judge McNeill made factual findings regarding plaintiff\'s income that were contradicted by documentary evidence, and selectively applied facts to support predetermined outcomes.',
    evidence: [
      'Income findings contradicted by tax returns and employment records',
      'Rental income claimed without documentary support',
      'Child support calculations based on misrepresented income figures',
      'Selective citation of evidence supporting defendant\'s position'
    ],
    impact: 'Child support obligations calculated on false income figures; plaintiff\'s legitimate evidence ignored; orders based on inaccurate factual record'
  },
  {
    id: 'pattern-5',
    title: 'Denial of Opportunity to Be Heard and Procedural Irregularities',
    severity: 'HIGH',
    legalBasis: ['MCR 3.206', '14th Amendment Due Process', 'MCL 722.27'],
    description: 'Judge McNeill consistently denied plaintiff meaningful opportunity to be heard, including ex parte modifications, filings under incorrect party names, and failure to ensure notice.',
    evidence: [
      'Ex parte parenting time modifications without notice to plaintiff',
      'Filings processed under incorrect party names without correction',
      'Hearings scheduled without adequate notice to plaintiff',
      'Plaintiff\'s objections and motions not addressed on the record'
    ],
    impact: 'Plaintiff denied fundamental due process; unable to contest allegations or present evidence; parenting time modified without notice or opportunity to respond'
  }
];

const motionTemplate: MotionSection[] = [
  {
    id: 'caption',
    title: 'CAPTION',
    content: `ANDREW J. PIGORS,
                                                    Plaintiff,

v.                                                  Case No. 2024-0000001507-DC

EMILY WATSON, et al.,
                                                    Defendant.
_____________________________________________/

MOTION FOR DISQUALIFICATION OF JUDGE PURSUANT TO MCL 600.1521 AND MCR 2.003`,
    required: true
  },
  {
    id: 'introduction',
    title: 'INTRODUCTION',
    content: `Plaintiff, by and through undersigned counsel, respectfully submits this Motion for Disqualification of the Honorable Jenny L. McNeill, requesting that the Court disqualify Judge McNeill from further proceedings in this matter pursuant to MCL 600.1521 and MCR 2.003.

This motion is supported by a well-founded and reasonable doubt regarding Judge McNeill's impartiality, based upon a clear and convincing pattern of judicial conduct that demonstrates systematic bias favoring the opposing party and consistent disadvantaging of the plaintiff.`,
    required: true
  },
  {
    id: 'legal-standard',
    title: 'LEGAL STANDARD FOR DISQUALIFICATION',
    content: `Under MCL 600.1521, a judge must disqualify himself or herself in any case in which the judge's impartiality might reasonably be questioned. MCR 2.003 similarly requires disqualification when a reasonable, well-founded doubt exists regarding the judge's impartiality.

The Michigan Supreme Court has established that a pattern of rulings favoring one party can establish judicial bias sufficient to warrant disqualification. In re Disqualification of Judge Giddings, 236 Mich. App. 261 (1999). Judicial bias includes systematic disadvantaging of one party through procedural irregularities and selective application of law. In re Disqualification of Judge Mahrle, 197 Mich. App. 229 (1992).

A reasonable, well-founded doubt regarding impartiality may be inferred from a pattern of rulings, not merely individual decisions. People v. Ezzard, 321 Mich. App. 1 (2018). The cumulative effect of multiple instances of questionable judicial conduct can establish grounds for disqualification even where individual instances might be defensible.`,
    required: true
  },
  {
    id: 'pattern-1',
    title: 'PATTERN 1: EX PARTE ORDERS WITHOUT AFFIDAVITS OR FINDINGS OF FACT',
    content: `Judge McNeill has repeatedly issued parenting time suspension and modification orders via telephone without requiring affidavits, written findings of fact, or documented emergency circumstances. This conduct violates MCR 3.206(A) and MCL 722.27(1)(c), which mandate specific procedural safeguards for emergency parenting time orders.

Specifically, on June 15, 2024, Judge McNeill ordered suspension of plaintiff's parenting time via telephone without:
- Any affidavit filed by opposing counsel
- Any written findings of fact explaining the emergency circumstances
- Any documented emergency justifying ex parte action
- Any opportunity for plaintiff to be heard

Subsequent orders referenced a HealthWest evaluation without formal submission to the court. This pattern of ex parte orders without required procedural safeguards demonstrates a systematic disregard for plaintiff's due process rights and suggests predetermined bias against the plaintiff.`,
    required: true
  },
  {
    id: 'pattern-2',
    title: 'PATTERN 2: DENIAL OF PARENTING TIME MODIFICATION DUE TO SANCTION FEE BARRIER',
    content: `Judge McNeill has imposed a $250 sanction fee as a barrier to filing parenting time modification motions, effectively denying plaintiff's constitutional right to petition the court for modification of custody and parenting time arrangements.

When plaintiff attempted to file a motion for modification of parenting time, Judge McNeill denied the motion based solely on the unpaid sanction fee, rather than addressing the merits of the modification request. This conduct violates MCR 3.203 and the due process guarantee of access to courts established in Boddie v. Connecticut, 401 U.S. 371 (1971).

The fee barrier has had concrete consequences: plaintiff has been unable to modify parenting time arrangements despite changed circumstances, resulting in employment loss and disruption of childcare arrangements. The use of fees as punitive barriers to statutory modification rights constitutes an abuse of judicial authority and demonstrates bias against the plaintiff.`,
    required: true
  },
  {
    id: 'pattern-3',
    title: 'PATTERN 3: DELAYED HEARINGS AND NOTICE FAILURES',
    content: `Judge McNeill has consistently delayed hearings on parenting time matters beyond reasonable timeframes and failed to provide adequate notice of hearing dates and modifications. These delays violate MCR 3.203, which requires expedited scheduling of custody and parenting time matters.

Specific instances include:
- Modification motions filed without timely hearing scheduling (delays exceeding 30 days)
- Notice of hearing modifications provided without sufficient advance notice to plaintiff
- Parenting time changes implemented without proper notice to plaintiff
- Inadequate time for plaintiff to prepare responses and gather evidence

These systematic delays and notice failures have prejudiced plaintiff's ability to prepare adequate responses and have destabilized plaintiff's employment and childcare arrangements. The pattern suggests deliberate delay designed to disadvantage the plaintiff.`,
    required: true
  },
  {
    id: 'pattern-4',
    title: 'PATTERN 4: MISREPRESENTED INCOME AND SELECTIVE FACT-FINDING',
    content: `Judge McNeill has made factual findings regarding plaintiff's income that are directly contradicted by documentary evidence in the record, and has selectively applied facts to support predetermined outcomes favoring the opposing party.

Specifically, Judge McNeill found that plaintiff's income included rental income and other sources not supported by tax returns or employment records. These income findings were used to calculate child support obligations that exceed plaintiff's actual documented income. When plaintiff presented contradictory evidence (tax returns, employment records, bank statements), Judge McNeill failed to address or acknowledge this evidence.

This selective fact-finding violates MCL 722.27(1)(c), which requires findings based on clear and convincing evidence. The pattern of ignoring plaintiff's evidence while accepting defendant's unsupported claims demonstrates bias and abuse of judicial authority.`,
    required: true
  },
  {
    id: 'pattern-5',
    title: 'PATTERN 5: DENIAL OF OPPORTUNITY TO BE HEARD AND PROCEDURAL IRREGULARITIES',
    content: `Judge McNeill has consistently denied plaintiff meaningful opportunity to be heard, including through ex parte modifications, processing filings under incorrect party names, and failure to ensure plaintiff received notice of proceedings.

Specific instances include:
- Ex parte parenting time modifications without notice to plaintiff
- Filings processed under incorrect party names without correction
- Hearings scheduled without adequate notice to plaintiff
- Plaintiff's objections and motions not addressed on the record
- Frivolous motions by opposing counsel not sanctioned despite pattern

These procedural irregularities violate MCR 3.206(C), which requires notice to all parties before parenting time modifications, and violate the due process guarantee of notice and opportunity to be heard established in Mathews v. Eldridge, 424 U.S. 319 (1976).`,
    required: true
  },
  {
    id: 'cumulative-pattern',
    title: 'CUMULATIVE PATTERN OF BIAS',
    content: `When considered together, the five patterns documented above establish a clear and convincing pattern of judicial bias favoring the opposing party and systematically disadvantaging the plaintiff. The patterns demonstrate:

1. Systematic Procedural Violations: Repeated ex parte actions without required procedural safeguards
2. Abuse of Judicial Authority: Use of sanctions and fees as barriers to statutory rights
3. Selective Fact-Finding: Factual findings contradicted by evidence in the record
4. Denial of Due Process: Consistent failure to provide notice and opportunity to be heard
5. Pattern of Favoritism: All violations benefited the opposing party; all disadvantaged the plaintiff

This cumulative pattern cannot be explained by individual judicial errors or discretionary decisions. Rather, the pattern demonstrates a systematic approach to disadvantaging the plaintiff and favoring the opposing party, creating a reasonable, well-founded doubt regarding Judge McNeill's impartiality.`,
    required: true
  },
  {
    id: 'conclusion',
    title: 'CONCLUSION',
    content: `For the foregoing reasons, plaintiff respectfully requests that this Court disqualify the Honorable Jenny L. McNeill from further proceedings in this matter and assign the case to a different judge.

Plaintiff further requests that all orders issued by Judge McNeill be reconsidered by the assigned judge, and that plaintiff's parenting time be restored to the status prior to the unlawful suspension.

Respectfully submitted,

_______________________________
Andrew J. Pigors, Plaintiff
[Date]`,
    required: true
  }
];

export function JudicialDisqualificationBuilder() {
  const [selectedPatterns, setSelectedPatterns] = useState<string[]>(
    biasPatterns.map(p => p.id)
  );
  const [motionText, setMotionText] = useState<string>('');
  const [viewMode, setViewMode] = useState<'builder' | 'preview' | 'draft'>('builder');

  const togglePattern = (patternId: string) => {
    setSelectedPatterns(prev =>
      prev.includes(patternId)
        ? prev.filter(id => id !== patternId)
        : [...prev, patternId]
    );
  };

  const generateMotion = () => {
    let motion = '';

    // Add all required sections
    motionTemplate.forEach(section => {
      motion += `${section.content}\n\n`;
    });

    // Add selected patterns
    const selected = biasPatterns.filter(p => selectedPatterns.includes(p.id));
    if (selected.length > 0) {
      motion += `\n\n--- SUPPORTING EVIDENCE FOR SELECTED PATTERNS ---\n\n`;
      selected.forEach(pattern => {
        motion += `${pattern.title}\n`;
        motion += `Severity: ${pattern.severity}\n`;
        motion += `Legal Basis: ${pattern.legalBasis.join(', ')}\n\n`;
        motion += `Description: ${pattern.description}\n\n`;
        motion += `Evidence:\n`;
        pattern.evidence.forEach(e => motion += `- ${e}\n`);
        motion += `\nImpact: ${pattern.impact}\n\n`;
      });
    }

    setMotionText(motion);
    toast.success('Motion generated successfully');
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(motionText);
    toast.success('Motion copied to clipboard');
  };

  const downloadMotion = () => {
    const element = document.createElement('a');
    element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(motionText));
    element.setAttribute('download', 'Motion_for_Disqualification_Judge_McNeill.txt');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
    toast.success('Motion downloaded');
  };

  const criticalCount = selectedPatterns.filter(id =>
    biasPatterns.find(p => p.id === id && p.severity === 'CRITICAL')
  ).length;

  const highCount = selectedPatterns.filter(id =>
    biasPatterns.find(p => p.id === id && p.severity === 'HIGH')
  ).length;

  return (
    <div className="space-y-6">
      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Patterns</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{biasPatterns.length}</div>
            <p className="text-xs text-muted-foreground mt-1">Documented bias patterns</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Critical Patterns</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-destructive">{criticalCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Selected for motion</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">High Severity</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{highCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Selected for motion</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Motion Status</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-semibold">{motionText ? 'Generated' : 'Ready'}</div>
            <p className="text-xs text-muted-foreground mt-1">Click Generate to create</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs value={viewMode} onValueChange={(v: any) => setViewMode(v)}>
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="builder">Pattern Builder</TabsTrigger>
          <TabsTrigger value="preview">Preview</TabsTrigger>
          <TabsTrigger value="draft">Draft Motion</TabsTrigger>
        </TabsList>

        {/* Pattern Builder Tab */}
        <TabsContent value="builder" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Select Bias Patterns</CardTitle>
              <CardDescription>Choose which patterns to include in the motion</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {biasPatterns.map(pattern => (
                <div key={pattern.id} className="border rounded-lg p-4">
                  <div className="flex items-start gap-3">
                    <Checkbox
                      id={pattern.id}
                      checked={selectedPatterns.includes(pattern.id)}
                      onCheckedChange={() => togglePattern(pattern.id)}
                      className="mt-1"
                    />
                    <div className="flex-1">
                      <label
                        htmlFor={pattern.id}
                        className="font-semibold text-sm cursor-pointer flex items-center gap-2"
                      >
                        {pattern.title}
                        <Badge
                          variant={pattern.severity === 'CRITICAL' ? 'destructive' : 'secondary'}
                          className="text-xs"
                        >
                          {pattern.severity}
                        </Badge>
                      </label>
                      <p className="text-sm text-muted-foreground mt-2">{pattern.description}</p>

                      <div className="mt-3 space-y-2">
                        <p className="text-xs font-semibold">Legal Basis:</p>
                        <div className="flex flex-wrap gap-1">
                          {pattern.legalBasis.map((basis, idx) => (
                            <Badge key={idx} variant="outline" className="text-xs">
                              {basis}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="mt-3">
                        <p className="text-xs font-semibold mb-1">Key Evidence:</p>
                        <ul className="text-xs text-muted-foreground space-y-1">
                          {pattern.evidence.slice(0, 2).map((e, idx) => (
                            <li key={idx}>• {e}</li>
                          ))}
                          {pattern.evidence.length > 2 && (
                            <li>• +{pattern.evidence.length - 2} more</li>
                          )}
                        </ul>
                      </div>

                      <p className="text-xs text-muted-foreground mt-2 italic">Impact: {pattern.impact}</p>
                    </div>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>

          <Button onClick={generateMotion} size="lg" className="w-full">
            <FileText className="w-4 h-4 mr-2" />
            Generate Motion
          </Button>
        </TabsContent>

        {/* Preview Tab */}
        <TabsContent value="preview" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Motion Structure Preview</CardTitle>
              <CardDescription>Overview of motion sections and content</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {motionTemplate.map(section => (
                <div key={section.id} className="border rounded-lg p-4">
                  <h4 className="font-semibold text-sm mb-2">{section.title}</h4>
                  <p className="text-sm text-muted-foreground line-clamp-3">{section.content}</p>
                  <Badge className="mt-2" variant={section.required ? 'default' : 'secondary'}>
                    {section.required ? 'Required' : 'Optional'}
                  </Badge>
                </div>
              ))}

              <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-200">
                <div className="flex gap-2">
                  <Scale className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                  <div>
                    <p className="font-semibold text-sm text-blue-900">Motion Components</p>
                    <p className="text-sm text-blue-800 mt-1">
                      This motion includes all required sections per MCL 600.1521 and MCR 2.003, plus detailed analysis of each selected bias pattern with supporting evidence and legal citations.
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Draft Motion Tab */}
        <TabsContent value="draft" className="space-y-6">
          {motionText ? (
            <>
              <div className="flex gap-2">
                <Button onClick={copyToClipboard} variant="outline" className="flex-1">
                  <Copy className="w-4 h-4 mr-2" />
                  Copy to Clipboard
                </Button>
                <Button onClick={downloadMotion} variant="outline" className="flex-1">
                  <Download className="w-4 h-4 mr-2" />
                  Download
                </Button>
              </div>

              <Card className="max-h-[600px] overflow-y-auto">
                <CardContent className="pt-6">
                  <pre className="text-xs whitespace-pre-wrap font-mono text-muted-foreground">
                    {motionText}
                  </pre>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8">
                  <FileText className="w-12 h-12 text-muted-foreground mx-auto mb-3 opacity-50" />
                  <p className="text-muted-foreground">No motion generated yet</p>
                  <p className="text-sm text-muted-foreground mt-1">
                    Select patterns and click "Generate Motion" to create the draft
                  </p>
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>

      {/* Legal Notice */}
      <Card className="bg-amber-50 border-amber-200">
        <CardHeader>
          <CardTitle className="text-sm flex items-center gap-2">
            <AlertTriangle className="w-4 h-4 text-amber-600" />
            Legal Notice
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-amber-900">
          <p>This motion is generated based on documented judicial conduct patterns and applicable Michigan law. All factual allegations must be supported by evidence in the record. This tool provides a template and framework; attorney review and customization is required before filing.</p>
        </CardContent>
      </Card>
    </div>
  );
}
