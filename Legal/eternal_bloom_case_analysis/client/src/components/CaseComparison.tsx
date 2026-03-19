import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cases, CaseProfile } from '@/data/cases';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, Cell } from 'recharts';
import { Scale, Users, FileText, Calendar, AlertCircle } from 'lucide-react';

export function CaseComparison() {
  // Prepare comparison data
  const comparisonData = cases.map((c) => ({
    name: c.name.split(' v. ')[0].substring(0, 15),
    issues: c.legalIssues.length,
    facts: c.facts.length,
    citations: c.citations.length,
    exhibits: c.exhibits.length,
    defendants: c.defendants.length,
  }));

  const caseMetrics = cases.map((c) => ({
    id: c.id,
    name: c.name,
    court: c.court.split(',')[0],
    plaintiff: c.plaintiff,
    defendantCount: c.defendants.length,
    issueCount: c.legalIssues.length,
    filingDate: c.filingDate,
    status: c.status,
    color: c.color,
  }));

  return (
    <div className="space-y-6">
      {/* Overview Comparison */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Scale className="w-6 h-6 text-accent" />
            Multi-Case Comparison
          </CardTitle>
          <CardDescription>
            Side-by-side analysis of {cases.length} related litigation matters
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Chart */}
          <div className="h-80 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Bar dataKey="issues" fill="#1e40af" name="Legal Issues" />
                <Bar dataKey="facts" fill="#dc2626" name="Facts" />
                <Bar dataKey="citations" fill="#7c3aed" name="Citations" />
                <Bar dataKey="defendants" fill="#16a34a" name="Defendants" />
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Detailed Comparison Table */}
          <Tabs defaultValue="overview" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="overview">Overview</TabsTrigger>
              <TabsTrigger value="parties">Parties</TabsTrigger>
              <TabsTrigger value="issues">Legal Issues</TabsTrigger>
            </TabsList>

            {/* Overview Tab */}
            <TabsContent value="overview" className="space-y-4">
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {caseMetrics.map((metric) => (
                    <div key={metric.id} className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow">
                      <div className="flex items-start justify-between gap-4 mb-3">
                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground">{metric.name}</h3>
                          <p className="text-sm text-muted-foreground mt-1">{metric.court}</p>
                        </div>
                        <div
                          className="w-4 h-4 rounded-full flex-shrink-0"
                          style={{ backgroundColor: metric.color }}
                        />
                      </div>

                      <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mb-3">
                        <div>
                          <p className="text-xs text-muted-foreground">Plaintiff</p>
                          <p className="text-sm font-medium text-foreground">{metric.plaintiff}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Defendants</p>
                          <p className="text-sm font-medium text-foreground">{metric.defendantCount}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Issues</p>
                          <p className="text-sm font-medium text-foreground">{metric.issueCount}</p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground">Filed</p>
                          <p className="text-sm font-medium text-foreground">{metric.filingDate}</p>
                        </div>
                      </div>

                      <Badge variant="outline" className="text-xs">
                        {metric.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Parties Tab */}
            <TabsContent value="parties" className="space-y-4">
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {cases.map((caseItem) => (
                    <div key={caseItem.id} className="p-4 rounded-lg border border-border">
                      <h3 className="font-semibold text-foreground mb-3">{caseItem.name}</h3>

                      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                        <div className="p-3 rounded bg-accent/10 border border-accent/20">
                          <p className="text-xs text-muted-foreground mb-2 font-semibold">Plaintiff</p>
                          <p className="text-sm text-foreground">{caseItem.plaintiff}</p>
                        </div>

                        <div className="p-3 rounded bg-destructive/10 border border-destructive/20">
                          <p className="text-xs text-muted-foreground mb-2 font-semibold">Defendants</p>
                          <ul className="space-y-1">
                            {caseItem.defendants.map((def) => (
                              <li key={def} className="text-sm text-foreground">
                                {def}
                              </li>
                            ))}
                          </ul>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* Issues Tab */}
            <TabsContent value="issues" className="space-y-4">
              <ScrollArea className="h-[600px] pr-4">
                <div className="space-y-4">
                  {cases.map((caseItem) => (
                    <div key={caseItem.id} className="p-4 rounded-lg border border-border">
                      <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                        <FileText className="w-4 h-4 text-accent" />
                        {caseItem.name}
                      </h3>

                      <div className="space-y-2">
                        {caseItem.legalIssues.map((issue, idx) => (
                          <div key={idx} className="flex gap-2 text-sm">
                            <span className="text-accent flex-shrink-0">•</span>
                            <span className="text-foreground">{issue}</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Relationship Map */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-6 h-6 text-accent" />
            Case Relationships & Overlapping Parties
          </CardTitle>
          <CardDescription>
            How the four cases are interconnected
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Shady Oaks MHP Connection */}
            <div className="p-4 rounded-lg border-2 border-blue-200 bg-blue-50 dark:bg-blue-950/20 dark:border-blue-800">
              <h3 className="font-semibold text-foreground mb-2">🏢 Shady Oaks MHP LLC</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Appears as defendant in 3 cases - central to the litigation web
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Pigors v. Shady Oaks</Badge>
                <Badge variant="outline">HOA MI v. Shady Oaks</Badge>
                <Badge variant="outline">Watson v. Shady Oaks</Badge>
              </div>
            </div>

            {/* VRM Capital Connection */}
            <div className="p-4 rounded-lg border-2 border-red-200 bg-red-50 dark:bg-red-950/20 dark:border-red-800">
              <h3 className="font-semibold text-foreground mb-2">💼 VRM Capital Corp</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Financial entity involved in multiple property disputes
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Pigors v. Shady Oaks</Badge>
                <Badge variant="outline">HOA MI v. Shady Oaks</Badge>
              </div>
            </div>

            {/* HOA MI Retail Homes Connection */}
            <div className="p-4 rounded-lg border-2 border-purple-200 bg-purple-50 dark:bg-purple-950/20 dark:border-purple-800">
              <h3 className="font-semibold text-foreground mb-2">🏛️ HOA MI Retail Homes LLC</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Plaintiff in 2 cases - pursuing multiple ownership disputes
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">HOA MI v. Shady Oaks (2025-0000000509-CZ)</Badge>
                <Badge variant="outline">HOA MI v. Lincoln Park</Badge>
              </div>
            </div>

            {/* Attorney Connection */}
            <div className="p-4 rounded-lg border-2 border-green-200 bg-green-50 dark:bg-green-950/20 dark:border-green-800">
              <h3 className="font-semibold text-foreground mb-2">⚖️ Jeremy R.M. Piper, Attorney</h3>
              <p className="text-sm text-muted-foreground mb-3">
                Represents HOA MI Retail Homes LLC in ownership disputes
              </p>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">HOA MI v. Shady Oaks</Badge>
                <Badge variant="outline">HOA MI v. Lincoln Park</Badge>
              </div>
            </div>
          </div>

          {/* Key Insights */}
          <div className="mt-6 p-4 bg-accent/10 rounded-lg border border-accent/20 space-y-2">
            <p className="text-sm font-semibold text-foreground">Key Insights:</p>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>• <strong>Shady Oaks MHP</strong> is the central defendant in 3 of 4 cases</li>
              <li>• <strong>VRM Capital Corp</strong> appears to be the financial entity controlling Shady Oaks</li>
              <li>• <strong>HOA MI Retail Homes</strong> is pursuing parallel litigation for mobile home ownership rights</li>
              <li>• <strong>Multiple courts</strong> are handling related matters (60th District & 14th Circuit)</li>
              <li>• <strong>Common legal themes</strong>: Habitability, retaliation, property rights, corporate liability</li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
