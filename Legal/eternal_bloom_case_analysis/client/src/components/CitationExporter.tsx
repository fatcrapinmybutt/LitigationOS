import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Download, FileText, Copy, Check } from 'lucide-react';
import { toast } from 'sonner';

interface CitationExportItem {
  id: string;
  name: string;
  bluebook: string;
  alwd: string;
  apa: string;
}

interface CitationExporterProps {
  citations: CitationExportItem[];
}

export function CitationExporter({ citations }: CitationExporterProps) {
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [selectedFormat, setSelectedFormat] = useState<'bluebook' | 'alwd' | 'apa'>('bluebook');

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text).then(() => {
      setCopiedId(id);
      toast.success('Citation copied to clipboard!');
      setTimeout(() => setCopiedId(null), 2000);
    });
  };

  const downloadAsText = (format: 'bluebook' | 'alwd' | 'apa') => {
    const content = citations
      .map((c) => c[format])
      .join('\n\n');

    const element = document.createElement('a');
    element.setAttribute(
      'href',
      `data:text/plain;charset=utf-8,${encodeURIComponent(content)}`
    );
    element.setAttribute('download', `citations_${format}.txt`);
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast.success(`Downloaded ${format.toUpperCase()} citations!`);
  };

  const downloadAsMarkdown = () => {
    const content = `# Legal Citations

## Bluebook Format
${citations.map((c) => `- ${c.bluebook}`).join('\n')}

## ALWD Format
${citations.map((c) => `- ${c.alwd}`).join('\n')}

## APA Format
${citations.map((c) => `- ${c.apa}`).join('\n')}
`;

    const element = document.createElement('a');
    element.setAttribute(
      'href',
      `data:text/markdown;charset=utf-8,${encodeURIComponent(content)}`
    );
    element.setAttribute('download', 'citations.md');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast.success('Downloaded citations as Markdown!');
  };

  const downloadAsJSON = () => {
    const element = document.createElement('a');
    element.setAttribute(
      'href',
      `data:application/json;charset=utf-8,${encodeURIComponent(JSON.stringify(citations, null, 2))}`
    );
    element.setAttribute('download', 'citations.json');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);

    toast.success('Downloaded citations as JSON!');
  };

  if (citations.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Citation Exporter</CardTitle>
          <CardDescription>Export and download selected citations</CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">No citations selected. Select authorities to export.</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Download className="w-6 h-6 text-accent" />
          Citation Exporter
        </CardTitle>
        <CardDescription>
          Export {citations.length} citation{citations.length !== 1 ? 's' : ''} in multiple formats
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Format Tabs */}
        <Tabs value={selectedFormat} onValueChange={(v) => setSelectedFormat(v as any)}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="bluebook">Bluebook</TabsTrigger>
            <TabsTrigger value="alwd">ALWD</TabsTrigger>
            <TabsTrigger value="apa">APA</TabsTrigger>
          </TabsList>

          {(['bluebook', 'alwd', 'apa'] as const).map((format) => (
            <TabsContent key={format} value={format} className="space-y-3">
              <div className="space-y-2 max-h-96 overflow-y-auto">
                {citations.map((citation) => (
                  <div
                    key={citation.id}
                    className="p-3 rounded-lg border border-border bg-secondary/20 flex items-start gap-2"
                  >
                    <code className="flex-1 text-xs bg-background p-2 rounded border border-border text-foreground overflow-x-auto">
                      {citation[format]}
                    </code>
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => copyToClipboard(citation[format], citation.id)}
                      className="flex-shrink-0"
                    >
                      {copiedId === citation.id ? (
                        <Check className="w-4 h-4" />
                      ) : (
                        <Copy className="w-4 h-4" />
                      )}
                    </Button>
                  </div>
                ))}
              </div>

              <Button
                onClick={() => downloadAsText(format)}
                className="w-full"
                variant="default"
              >
                <Download className="w-4 h-4 mr-2" />
                Download {format.toUpperCase()} as Text
              </Button>
            </TabsContent>
          ))}
        </Tabs>

        {/* Additional Export Options */}
        <div className="space-y-2 pt-4 border-t border-border">
          <p className="text-sm font-semibold text-foreground">Additional Export Formats</p>
          <div className="grid grid-cols-2 gap-2">
            <Button
              onClick={downloadAsMarkdown}
              variant="outline"
              className="w-full"
            >
              <FileText className="w-4 h-4 mr-2" />
              Markdown
            </Button>
            <Button
              onClick={downloadAsJSON}
              variant="outline"
              className="w-full"
            >
              <FileText className="w-4 h-4 mr-2" />
              JSON
            </Button>
          </div>
        </div>

        {/* Statistics */}
        <div className="p-3 bg-accent/10 rounded-lg border border-accent/20">
          <p className="text-sm text-foreground">
            <strong>{citations.length}</strong> citation{citations.length !== 1 ? 's' : ''} ready to export
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
