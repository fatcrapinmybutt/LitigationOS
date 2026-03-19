import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  relationshipTimeline,
  timelineStatistics,
  getEventsForCase,
  getEventsBySeverity,
} from '@/data/relationship_timeline';
import { multiCaseTracks } from '@/data/multi_case_data';
import { Calendar, AlertCircle, TrendingUp, Zap } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, BarChart, Bar, Cell } from 'recharts';

export function RelationshipTimeline() {
  const [selectedCase, setSelectedCase] = useState<string | null>(null);
  const [selectedSeverity, setSelectedSeverity] = useState<'all' | 'critical' | 'high' | 'medium' | 'low'>('all');
  const [viewMode, setViewMode] = useState<'chronological' | 'by-case' | 'by-severity'>('chronological');

  // Filter events based on selections
  const filteredEvents = relationshipTimeline.filter((event) => {
    const matchesSeverity = selectedSeverity === 'all' || event.severity === selectedSeverity;
    const matchesCase = !selectedCase || event.cases.includes(selectedCase) || event.relatedCases?.includes(selectedCase);
    return matchesSeverity && matchesCase;
  });

  // Prepare chart data
  const eventsByMonth = relationshipTimeline.reduce((acc, event) => {
    const month = event.date.substring(0, 7); // YYYY-MM
    const existing = acc.find((item) => item.month === month);
    if (existing) {
      existing.events += 1;
    } else {
      acc.push({ month, events: 1 });
    }
    return acc;
  }, [] as Array<{ month: string; events: number }>);

  const severityData = [
    { name: 'Critical', value: timelineStatistics.criticalEvents, fill: '#EF4444' },
    { name: 'High', value: timelineStatistics.highEvents, fill: '#F97316' },
    { name: 'Medium', value: timelineStatistics.mediumEvents, fill: '#EAB308' },
    { name: 'Low', value: timelineStatistics.lowEvents, fill: '#6B7280' },
  ];

  return (
    <div className="space-y-6">
      {/* Timeline Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{timelineStatistics.totalEvents}</div>
            <p className="text-xs text-muted-foreground mt-1">Relationship milestones</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Critical Events</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{timelineStatistics.criticalEvents}</div>
            <p className="text-xs text-muted-foreground mt-1">Require attention</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Timeline Span</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-foreground">
              {timelineStatistics.timelineStart} to {timelineStatistics.timelineEnd}
            </div>
            <p className="text-xs text-muted-foreground mt-1">~9 months</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">First Connection</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-lg font-bold text-foreground">{timelineStatistics.connectionEstablishmentDate}</div>
            <p className="text-xs text-muted-foreground mt-1">Network established</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="chronological" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="chronological">Chronological</TabsTrigger>
          <TabsTrigger value="by-case">By Case</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
          <TabsTrigger value="connections">Connections</TabsTrigger>
        </TabsList>

        {/* Chronological Timeline */}
        <TabsContent value="chronological" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Calendar className="w-6 h-6 text-accent" />
                Relationship Timeline
              </CardTitle>
              <CardDescription>Chronological view of case connections and shared events</CardDescription>
            </CardHeader>
            <CardContent>
              {/* Severity Filter */}
              <div className="mb-6 flex flex-wrap gap-2">
                <button
                  onClick={() => setSelectedSeverity('all')}
                  className={`px-3 py-1 rounded-full text-sm transition-all ${
                    selectedSeverity === 'all'
                      ? 'bg-accent text-accent-foreground'
                      : 'bg-secondary text-secondary-foreground hover:bg-accent/20'
                  }`}
                >
                  All Events
                </button>
                {(['critical', 'high', 'medium', 'low'] as const).map((severity) => (
                  <button
                    key={severity}
                    onClick={() => setSelectedSeverity(severity)}
                    className={`px-3 py-1 rounded-full text-sm transition-all capitalize ${
                      selectedSeverity === severity
                        ? 'bg-accent text-accent-foreground'
                        : 'bg-secondary text-secondary-foreground hover:bg-accent/20'
                    }`}
                  >
                    {severity}
                  </button>
                ))}
              </div>

              {/* Timeline */}
              <ScrollArea className="h-[700px]">
                <div className="space-y-4 pr-4">
                  {filteredEvents.map((event, idx) => (
                    <div key={event.id} className="relative pl-8">
                      {/* Timeline line */}
                      {idx < filteredEvents.length - 1 && (
                        <div className="absolute left-0 top-8 bottom-0 w-0.5 bg-gradient-to-b from-accent via-accent/50 to-accent/20" />
                      )}

                      {/* Timeline dot */}
                      <div
                        className="absolute left-0 top-2 w-4 h-4 rounded-full border-2 border-background transform -translate-x-1.5"
                        style={{
                          backgroundColor:
                            event.severity === 'critical'
                              ? '#EF4444'
                              : event.severity === 'high'
                                ? '#F97316'
                                : event.severity === 'medium'
                                  ? '#EAB308'
                                  : '#6B7280',
                        }}
                      />

                      {/* Event card */}
                      <div className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-xl">{event.icon}</span>
                              <p className="font-semibold text-foreground">{event.title}</p>
                            </div>
                            <p className="text-sm text-muted-foreground">{event.description}</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="font-bold text-foreground text-sm">{event.date}</p>
                            <Badge
                              className={
                                event.severity === 'critical'
                                  ? 'bg-red-100 text-red-800 mt-1'
                                  : event.severity === 'high'
                                    ? 'bg-orange-100 text-orange-800 mt-1'
                                    : event.severity === 'medium'
                                      ? 'bg-yellow-100 text-yellow-800 mt-1'
                                      : 'bg-gray-100 text-gray-800 mt-1'
                              }
                            >
                              {event.severity}
                            </Badge>
                          </div>
                        </div>

                        {/* Cases involved */}
                        <div className="mt-3 pt-3 border-t border-border/50">
                          <p className="text-xs font-semibold text-muted-foreground mb-2">Cases Involved:</p>
                          <div className="flex flex-wrap gap-1">
                            {event.cases.map((caseId) => {
                              const caseItem = multiCaseTracks.find((c) => c.id === caseId);
                              return (
                                <Badge key={caseId} variant="secondary" className="text-xs">
                                  {caseItem?.caseNumber}
                                </Badge>
                              );
                            })}
                          </div>
                        </div>

                        {/* Related cases */}
                        {event.relatedCases && event.relatedCases.length > 0 && (
                          <div className="mt-2 pt-2 border-t border-border/50">
                            <p className="text-xs font-semibold text-muted-foreground mb-2">Connected To:</p>
                            <div className="flex flex-wrap gap-1">
                              {event.relatedCases.map((caseId) => {
                                const caseItem = multiCaseTracks.find((c) => c.id === caseId);
                                return (
                                  <Badge key={caseId} variant="outline" className="text-xs">
                                    {caseItem?.caseNumber}
                                  </Badge>
                                );
                              })}
                            </div>
                          </div>
                        )}

                        {/* Parties and issues */}
                        {(event.parties || event.legalIssues) && (
                          <div className="mt-2 pt-2 border-t border-border/50 space-y-2">
                            {event.parties && (
                              <div>
                                <p className="text-xs font-semibold text-muted-foreground mb-1">Parties:</p>
                                <div className="flex flex-wrap gap-1">
                                  {event.parties.map((party, idx) => (
                                    <Badge key={idx} variant="secondary" className="text-xs">
                                      {party}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                            {event.legalIssues && (
                              <div>
                                <p className="text-xs font-semibold text-muted-foreground mb-1">Legal Issues:</p>
                                <div className="flex flex-wrap gap-1">
                                  {event.legalIssues.map((issue, idx) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {issue}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* By Case Timeline */}
        <TabsContent value="by-case" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Filter by Case</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <button
                  onClick={() => setSelectedCase(null)}
                  className={`p-3 rounded-lg border-2 transition-all text-left ${
                    selectedCase === null
                      ? 'border-accent bg-accent/10'
                      : 'border-border hover:border-accent/50'
                  }`}
                >
                  <p className="font-semibold text-foreground">All Cases</p>
                  <p className="text-sm text-muted-foreground mt-1">{relationshipTimeline.length} events</p>
                </button>

                {multiCaseTracks.map((caseItem) => {
                  const caseEvents = getEventsForCase(caseItem.id);
                  return (
                    <button
                      key={caseItem.id}
                      onClick={() => setSelectedCase(caseItem.id)}
                      className={`p-3 rounded-lg border-2 transition-all text-left ${
                        selectedCase === caseItem.id
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-accent/50'
                      }`}
                      style={{
                        borderLeftColor: caseItem.color,
                        borderLeftWidth: '4px',
                      }}
                    >
                      <p className="font-semibold text-foreground">{caseItem.caseNumber}</p>
                      <p className="text-sm text-muted-foreground mt-1">{caseEvents.length} events</p>
                    </button>
                  );
                })}
              </div>

              {/* Case-specific timeline */}
              {selectedCase && (
                <div className="mt-6 pt-6 border-t border-border">
                  <h3 className="font-semibold text-foreground mb-4">
                    Events for {multiCaseTracks.find((c) => c.id === selectedCase)?.caseNumber}
                  </h3>
                  <ScrollArea className="h-[400px]">
                    <div className="space-y-3 pr-4">
                      {getEventsForCase(selectedCase).map((event) => (
                        <div key={event.id} className="p-3 rounded-lg border border-border">
                          <div className="flex items-start justify-between gap-2 mb-2">
                            <div className="flex-1">
                              <p className="font-semibold text-foreground text-sm">{event.title}</p>
                              <p className="text-xs text-muted-foreground mt-1">{event.description}</p>
                            </div>
                            <p className="text-xs font-bold text-foreground">{event.date}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </ScrollArea>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Events Over Time */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Events Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={eventsByMonth}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="month" />
                    <YAxis />
                    <Tooltip />
                    <Line type="monotone" dataKey="events" stroke="#8884d8" strokeWidth={2} />
                  </LineChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Events by Severity */}
            <Card>
              <CardHeader>
                <CardTitle className="text-sm">Events by Severity</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={severityData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="value" fill="#8884d8">
                      {severityData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* Connections Tab */}
        <TabsContent value="connections" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Zap className="w-6 h-6 text-accent" />
                Key Connection Events
              </CardTitle>
              <CardDescription>Events that established relationships between cases</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4 pr-4">
                  {relationshipTimeline
                    .filter((e) => e.eventType === 'shared-party-appears' || e.eventType === 'connection-established')
                    .map((event) => (
                      <div key={event.id} className="p-4 rounded-lg border-2 border-accent/30 bg-accent/5">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <span className="text-2xl">{event.icon}</span>
                              <p className="font-semibold text-foreground">{event.title}</p>
                            </div>
                            <p className="text-sm text-muted-foreground">{event.description}</p>
                          </div>
                          <p className="font-bold text-foreground text-sm">{event.date}</p>
                        </div>

                        {/* Connected cases */}
                        <div className="mt-3 pt-3 border-t border-accent/20">
                          <p className="text-xs font-semibold text-muted-foreground mb-2">Connected Cases:</p>
                          <div className="flex flex-wrap gap-2">
                            {event.cases.map((caseId) => {
                              const caseItem = multiCaseTracks.find((c) => c.id === caseId);
                              return (
                                <Badge key={caseId} style={{ backgroundColor: caseItem?.color }}>
                                  {caseItem?.caseNumber}
                                </Badge>
                              );
                            })}
                          </div>
                        </div>

                        {/* Shared elements */}
                        {event.parties && (
                          <div className="mt-2 pt-2 border-t border-accent/20">
                            <p className="text-xs font-semibold text-muted-foreground mb-1">Shared Parties:</p>
                            <div className="flex flex-wrap gap-1">
                              {event.parties.map((party, idx) => (
                                <Badge key={idx} variant="secondary" className="text-xs">
                                  {party}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
