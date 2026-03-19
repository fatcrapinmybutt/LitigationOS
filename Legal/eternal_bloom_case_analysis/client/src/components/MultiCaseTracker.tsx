import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { multiCaseTracks, caseTypeCategories, caseStatistics, multiCaseTimeline } from '@/data/multi_case_data';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Calendar, FileText, Users, Gavel, TrendingUp } from 'lucide-react';
import { JurisdictionMap } from './JurisdictionMap';
import { CaseRelationshipGraph } from './CaseRelationshipGraph';
import { RelationshipTimeline } from './RelationshipTimeline';

export function MultiCaseTracker() {
  const [selectedCaseType, setSelectedCaseType] = useState<'all' | 'dc' | 'pp' | 'lt' | 'cz'>('all');
  const [selectedCase, setSelectedCase] = useState<string | null>(null);

  // Filter cases by type
  const filteredCases =
    selectedCaseType === 'all'
      ? multiCaseTracks
      : multiCaseTracks.filter((c) => c.caseType === selectedCaseType);

  // Prepare chart data
  const caseTypeChartData = [
    { name: 'District Court (DC)', value: caseStatistics.casesByType.dc, fill: caseTypeCategories.dc.color },
    { name: 'Probate/PP', value: caseStatistics.casesByType.pp, fill: caseTypeCategories.pp.color },
    { name: 'Landlord-Tenant (LT)', value: caseStatistics.casesByType.lt, fill: caseTypeCategories.lt.color },
    { name: 'Civil (CZ)', value: caseStatistics.casesByType.cz, fill: caseTypeCategories.cz.color },
  ];

  const statusChartData = [
    { name: 'Active', value: caseStatistics.activeCases },
    { name: 'Pending', value: caseStatistics.pendingCases },
    { name: 'Closed', value: caseStatistics.closedCases },
  ];

  return (
    <div className="space-y-6">
      {/* Overview Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{caseStatistics.totalCases}</div>
            <p className="text-xs text-muted-foreground mt-1">Across all case types</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Active Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-600">{caseStatistics.activeCases}</div>
            <p className="text-xs text-muted-foreground mt-1">Currently in progress</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Pending Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-yellow-600">{caseStatistics.pendingCases}</div>
            <p className="text-xs text-muted-foreground mt-1">Awaiting action</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Closed Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-gray-600">{caseStatistics.closedCases}</div>
            <p className="text-xs text-muted-foreground mt-1">Resolved</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="case-types" className="space-y-6">
        <TabsList className="grid w-full grid-cols-7">
          <TabsTrigger value="case-types">Case Types</TabsTrigger>
          <TabsTrigger value="all-cases">All Cases</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="jurisdictions">Jurisdictions</TabsTrigger>
          <TabsTrigger value="relationships">Relationships</TabsTrigger>
          <TabsTrigger value="rel-timeline">Rel. Timeline</TabsTrigger>
        </TabsList>

        {/* Case Types Tab */}
        <TabsContent value="case-types" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Gavel className="w-6 h-6 text-accent" />
                Case Type Categories
              </CardTitle>
              <CardDescription>Filter and view cases by type</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {Object.entries(caseTypeCategories).map(([key, category]) => (
                  <button
                    key={key}
                    onClick={() => setSelectedCaseType(key as any)}
                    className={`p-4 rounded-lg border-2 transition-all text-left ${
                      selectedCaseType === key
                        ? 'border-accent bg-accent/10'
                        : 'border-border hover:border-accent/50'
                    }`}
                  >
                    <div className="flex items-center gap-3 mb-2">
                      <span className="text-2xl">{category.icon}</span>
                      <h3 className="font-semibold text-foreground">{category.label}</h3>
                    </div>
                    <p className="text-sm text-muted-foreground">
                      {caseStatistics.casesByType[key as keyof typeof caseStatistics.casesByType]} case(s)
                    </p>
                  </button>
                ))}
              </div>

              <button
                onClick={() => setSelectedCaseType('all')}
                className={`w-full mt-4 p-4 rounded-lg border-2 transition-all ${
                  selectedCaseType === 'all'
                    ? 'border-accent bg-accent/10'
                    : 'border-border hover:border-accent/50'
                }`}
              >
                <h3 className="font-semibold text-foreground">View All Cases</h3>
                <p className="text-sm text-muted-foreground mt-1">
                  {caseStatistics.totalCases} total cases
                </p>
              </button>
            </CardContent>
          </Card>
        </TabsContent>

        {/* All Cases Tab */}
        <TabsContent value="all-cases" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="w-6 h-6 text-accent" />
                Case Details
              </CardTitle>
              <CardDescription>
                {selectedCaseType === 'all'
                  ? 'All cases'
                  : `${caseTypeCategories[selectedCaseType as keyof typeof caseTypeCategories].label} cases`}
              </CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4 pr-4">
                  {filteredCases.map((caseItem) => (
                    <div
                      key={caseItem.id}
                      onClick={() => setSelectedCase(caseItem.id)}
                      className={`p-4 rounded-lg border-2 cursor-pointer transition-all ${
                        selectedCase === caseItem.id
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-accent/50'
                      }`}
                      style={{
                        borderLeftColor: caseItem.color,
                        borderLeftWidth: '4px',
                      }}
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex-1">
                          <h3 className="font-semibold text-foreground">{caseItem.caseNumber}</h3>
                          <p className="text-sm text-muted-foreground mt-1">{caseItem.name}</p>
                        </div>
                        <Badge
                          className={`${
                            caseItem.status === 'active'
                              ? 'bg-green-100 text-green-800'
                              : caseItem.status === 'pending'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-gray-100 text-gray-800'
                          }`}
                        >
                          {caseItem.status}
                        </Badge>
                      </div>

                      <div className="grid grid-cols-2 gap-3 text-sm">
                        <div>
                          <p className="text-muted-foreground">Court</p>
                          <p className="font-medium text-foreground">{caseItem.court}</p>
                        </div>
                        <div>
                          <p className="text-muted-foreground">Type</p>
                          <p className="font-medium text-foreground">{caseItem.caseTypeLabel}</p>
                        </div>
                      </div>

                      {/* Parties */}
                      <div className="mt-3 pt-3 border-t border-border/50">
                        <p className="text-xs font-semibold text-muted-foreground mb-2">Parties</p>
                        <div className="space-y-1 text-xs">
                          <p className="text-foreground">
                            <strong>Plaintiff(s):</strong> {caseItem.parties.plaintiffs.join(', ')}
                          </p>
                          <p className="text-foreground">
                            <strong>Defendant(s):</strong> {caseItem.parties.defendants.join(', ')}
                          </p>
                        </div>
                      </div>

                      {/* Legal Issues */}
                      <div className="mt-3 flex flex-wrap gap-1">
                        {caseItem.legalIssues.slice(0, 3).map((issue, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {issue}
                          </Badge>
                        ))}
                        {caseItem.legalIssues.length > 3 && (
                          <Badge variant="secondary" className="text-xs">
                            +{caseItem.legalIssues.length - 3} more
                          </Badge>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>

          {/* Selected Case Details */}
          {selectedCase && (
            <Card>
              <CardHeader>
                <CardTitle>Case Details</CardTitle>
              </CardHeader>
              <CardContent>
                {multiCaseTracks
                  .filter((c) => c.id === selectedCase)
                  .map((caseItem) => (
                    <div key={caseItem.id} className="space-y-4">
                      <div>
                        <h3 className="font-semibold text-foreground mb-2">Key Dates</h3>
                        <div className="space-y-2">
                          {caseItem.keyDates.map((date, idx) => (
                            <div key={idx} className="flex justify-between text-sm">
                              <span className="text-muted-foreground">{date.event}</span>
                              <span className="font-medium text-foreground">{date.date}</span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div className="pt-4 border-t border-border">
                        <h3 className="font-semibold text-foreground mb-2">Legal Issues</h3>
                        <div className="flex flex-wrap gap-2">
                          {caseItem.legalIssues.map((issue, idx) => (
                            <Badge key={idx} variant="outline">
                              {issue}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="pt-4 border-t border-border">
                        <h3 className="font-semibold text-foreground mb-2">Exhibits</h3>
                        <div className="flex flex-wrap gap-2">
                          {caseItem.exhibits.map((exhibit, idx) => (
                            <Badge key={idx} variant="secondary">
                              {exhibit}
                            </Badge>
                          ))}
                        </div>
                      </div>

                      <div className="pt-4 border-t border-border">
                        <p className="text-sm text-muted-foreground italic">{caseItem.description}</p>
                      </div>
                    </div>
                  ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Case Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Cases by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={caseTypeChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {caseTypeChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Case Status Distribution */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Cases by Status</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={statusChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-6 h-6 text-accent" />
                Multi-Case Timeline
              </CardTitle>
              <CardDescription>Chronological view of all case events</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4 pr-4">
                  {multiCaseTimeline.map((event, idx) => {
                    const caseItem = multiCaseTracks.find((c) => c.id === event.caseId);
                    return (
                      <div key={idx} className="relative pl-8">
                        {/* Timeline line */}
                        <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-accent via-accent/50 to-accent/20" />

                        {/* Timeline dot */}
                        <div
                          className="absolute left-0 top-2 w-4 h-4 rounded-full border-2 border-background transform -translate-x-1.5"
                          style={{ backgroundColor: caseItem?.color }}
                        />

                        {/* Event card */}
                        <div className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow">
                          <div className="flex items-start justify-between gap-3 mb-2">
                            <div className="flex-1">
                              <p className="font-semibold text-foreground">{event.event}</p>
                              <p className="text-sm text-muted-foreground mt-1">{event.caseNumber}</p>
                            </div>
                            <p className="font-bold text-foreground text-sm">{event.date}</p>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Jurisdictions Tab */}
        <TabsContent value="jurisdictions" className="space-y-6">
          <JurisdictionMap />
        </TabsContent>

        {/* Relationships Tab */}
        <TabsContent value="relationships" className="space-y-6">
          <CaseRelationshipGraph />
        </TabsContent>

        {/* Relationship Timeline Tab */}
        <TabsContent value="rel-timeline" className="space-y-6">
          <RelationshipTimeline />
        </TabsContent>
      </Tabs>
    </div>
  );
}
