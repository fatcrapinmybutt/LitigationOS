import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cases } from '@/data/cases';
import { Calendar, AlertCircle, FileText, Users, Gavel } from 'lucide-react';

interface TimelineEvent {
  date: string;
  dateObj: Date;
  event: string;
  caseId: string;
  caseName: string;
  caseColor: string;
  eventType: 'filing' | 'hearing' | 'violation' | 'decision' | 'motion' | 'evidence' | 'other';
}

export function MasterTimeline() {
  // Consolidate all events from all cases
  const allEvents: TimelineEvent[] = [];

  cases.forEach((caseItem) => {
    caseItem.keyDates.forEach((keyDate) => {
      allEvents.push({
        date: keyDate.date,
        dateObj: new Date(keyDate.date),
        event: keyDate.event,
        caseId: caseItem.id,
        caseName: caseItem.name,
        caseColor: caseItem.color,
        eventType: determineEventType(keyDate.event),
      });
    });
  });

  // Sort chronologically
  allEvents.sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());

  // Group by month/year
  const groupedByMonth = groupEventsByMonth(allEvents);

  // Calculate timeline statistics
  const stats = {
    totalEvents: allEvents.length,
    uniqueDates: new Set(allEvents.map((e) => e.date)).size,
    dateRange: {
      start: allEvents[0]?.date || 'N/A',
      end: allEvents[allEvents.length - 1]?.date || 'N/A',
    },
    eventsByType: countEventsByType(allEvents),
    eventsByCase: countEventsByCase(allEvents),
  };

  return (
    <div className="space-y-6">
      {/* Master Timeline Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-6 h-6 text-accent" />
            Master Litigation Timeline
          </CardTitle>
          <CardDescription>
            Consolidated chronological view of all key dates across {cases.length} related cases
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Timeline Statistics */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <div className="p-3 rounded-lg bg-secondary/30 border border-border">
              <p className="text-xs text-muted-foreground mb-1">Total Events</p>
              <p className="text-2xl font-bold text-foreground">{stats.totalEvents}</p>
            </div>
            <div className="p-3 rounded-lg bg-secondary/30 border border-border">
              <p className="text-xs text-muted-foreground mb-1">Unique Dates</p>
              <p className="text-2xl font-bold text-foreground">{stats.uniqueDates}</p>
            </div>
            <div className="p-3 rounded-lg bg-secondary/30 border border-border">
              <p className="text-xs text-muted-foreground mb-1">Start Date</p>
              <p className="text-sm font-bold text-foreground">{stats.dateRange.start}</p>
            </div>
            <div className="p-3 rounded-lg bg-secondary/30 border border-border">
              <p className="text-xs text-muted-foreground mb-1">End Date</p>
              <p className="text-sm font-bold text-foreground">{stats.dateRange.end}</p>
            </div>
          </div>

          {/* Tabs for different views */}
          <Tabs defaultValue="chronological" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="chronological">Chronological</TabsTrigger>
              <TabsTrigger value="by-case">By Case</TabsTrigger>
              <TabsTrigger value="by-type">By Type</TabsTrigger>
            </TabsList>

            {/* Chronological View */}
            <TabsContent value="chronological" className="space-y-4">
              <ScrollArea className="h-[800px] pr-4">
                <div className="space-y-4">
                  {allEvents.map((event, idx) => (
                    <div key={`${event.date}-${idx}`} className="relative pl-8">
                      {/* Timeline line */}
                      <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-accent via-accent/50 to-accent/20" />

                      {/* Timeline dot */}
                      <div
                        className="absolute left-0 top-2 w-4 h-4 rounded-full border-2 border-background transform -translate-x-1.5"
                        style={{ backgroundColor: event.caseColor }}
                      />

                      {/* Event card */}
                      <div className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1">
                            <p className="font-semibold text-foreground">{event.event}</p>
                            <p className="text-sm text-muted-foreground mt-1">{event.caseName}</p>
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="font-bold text-foreground">{event.date}</p>
                            <Badge variant="outline" className="text-xs mt-1">
                              {event.eventType}
                            </Badge>
                          </div>
                        </div>

                        {/* Case indicator */}
                        <div className="flex items-center gap-2 mt-3">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: event.caseColor }}
                          />
                          <span className="text-xs text-muted-foreground">{event.caseId}</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* By Case View */}
            <TabsContent value="by-case" className="space-y-4">
              <ScrollArea className="h-[800px] pr-4">
                <div className="space-y-6">
                  {cases.map((caseItem) => {
                    const caseEvents = allEvents.filter((e) => e.caseId === caseItem.id);
                    return (
                      <div key={caseItem.id} className="space-y-3">
                        <div className="flex items-center gap-3 mb-3">
                          <div
                            className="w-4 h-4 rounded-full"
                            style={{ backgroundColor: caseItem.color }}
                          />
                          <h3 className="font-semibold text-foreground">{caseItem.name}</h3>
                          <Badge variant="outline" className="text-xs">
                            {caseEvents.length} events
                          </Badge>
                        </div>

                        <div className="space-y-2 pl-7 border-l-2 border-border">
                          {caseEvents.map((event, idx) => (
                            <div key={`${event.date}-${idx}`} className="p-3 rounded-lg bg-secondary/30 border border-border">
                              <div className="flex items-start justify-between gap-2">
                                <div className="flex-1">
                                  <p className="text-sm font-medium text-foreground">{event.event}</p>
                                  <p className="text-xs text-muted-foreground mt-1">{event.date}</p>
                                </div>
                                <Badge variant="outline" className="text-xs flex-shrink-0">
                                  {event.eventType}
                                </Badge>
                              </div>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </TabsContent>

            {/* By Type View */}
            <TabsContent value="by-type" className="space-y-4">
              <ScrollArea className="h-[800px] pr-4">
                <div className="space-y-6">
                  {Object.entries(stats.eventsByType).map(([type, count]) => {
                    const typeEvents = allEvents.filter((e) => e.eventType === type as any);
                    return (
                      <div key={type} className="space-y-3">
                        <div className="flex items-center gap-3 mb-3">
                          <h3 className="font-semibold text-foreground capitalize">{type}</h3>
                          <Badge variant="outline" className="text-xs">
                            {count} events
                          </Badge>
                        </div>

                        <div className="space-y-2 pl-4">
                          {typeEvents.map((event, idx) => (
                            <div key={`${event.date}-${idx}`} className="p-3 rounded-lg border border-border">
                              <div className="flex items-start justify-between gap-2 mb-2">
                                <p className="text-sm font-medium text-foreground">{event.event}</p>
                                <p className="text-xs text-muted-foreground font-mono">{event.date}</p>
                              </div>
                              <p className="text-xs text-muted-foreground">{event.caseName}</p>
                            </div>
                          ))}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Timeline Insights */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="w-6 h-6 text-accent" />
            Timeline Insights & Patterns
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Events by Type */}
            <div className="p-4 rounded-lg border border-border">
              <h3 className="font-semibold text-foreground mb-3">Events by Type</h3>
              <div className="space-y-2">
                {Object.entries(stats.eventsByType)
                  .sort(([, a], [, b]) => b - a)
                  .map(([type, count]) => (
                    <div key={type} className="flex items-center justify-between">
                      <span className="text-sm text-muted-foreground capitalize">{type}</span>
                      <div className="flex items-center gap-2">
                        <div className="h-2 bg-accent rounded-full" style={{ width: `${(count / stats.totalEvents) * 100}px` }} />
                        <span className="text-sm font-medium text-foreground">{count}</span>
                      </div>
                    </div>
                  ))}
              </div>
            </div>

            {/* Events by Case */}
            <div className="p-4 rounded-lg border border-border">
              <h3 className="font-semibold text-foreground mb-3">Events by Case</h3>
              <div className="space-y-2">
                {Object.entries(stats.eventsByCase)
                  .sort(([, a], [, b]) => b - a)
                  .map(([caseId, count]) => {
                    const caseItem = cases.find((c) => c.id === caseId);
                    return (
                      <div key={caseId} className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <div
                            className="w-3 h-3 rounded-full"
                            style={{ backgroundColor: caseItem?.color }}
                          />
                          <span className="text-sm text-muted-foreground">{caseItem?.name.split(' ')[0]}</span>
                        </div>
                        <div className="flex items-center gap-2">
                          <div className="h-2 bg-accent rounded-full" style={{ width: `${(count / stats.totalEvents) * 100}px` }} />
                          <span className="text-sm font-medium text-foreground">{count}</span>
                        </div>
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>

          {/* Key Observations */}
          <div className="p-4 bg-accent/10 rounded-lg border border-accent/20 space-y-2">
            <p className="text-sm font-semibold text-foreground">Key Observations:</p>
            <ul className="space-y-1 text-sm text-muted-foreground">
              <li>
                • <strong>Timeline Span:</strong> {stats.dateRange.start} to {stats.dateRange.end} ({calculateDaysDifference(stats.dateRange.start, stats.dateRange.end)} days)
              </li>
              <li>
                • <strong>Most Active Case:</strong> {getMostActiveCaseInfo(stats.eventsByCase, cases)}
              </li>
              <li>
                • <strong>Most Common Event Type:</strong> {getMostCommonEventType(stats.eventsByType)}
              </li>
              <li>
                • <strong>Litigation Intensity:</strong> {calculateLitigationIntensity(allEvents)} events per month on average
              </li>
              <li>
                • <strong>Critical Period:</strong> {identifyCriticalPeriod(allEvents)}
              </li>
            </ul>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

// Helper functions
function determineEventType(event: string): 'filing' | 'hearing' | 'violation' | 'decision' | 'motion' | 'evidence' | 'other' {
  const lowerEvent = event.toLowerCase();
  if (lowerEvent.includes('file') || lowerEvent.includes('filed')) return 'filing';
  if (lowerEvent.includes('hearing') || lowerEvent.includes('court')) return 'hearing';
  if (lowerEvent.includes('violation') || lowerEvent.includes('egle')) return 'violation';
  if (lowerEvent.includes('decision') || lowerEvent.includes('judgment')) return 'decision';
  if (lowerEvent.includes('motion')) return 'motion';
  if (lowerEvent.includes('evidence') || lowerEvent.includes('photo') || lowerEvent.includes('document')) return 'evidence';
  return 'other';
}

function groupEventsByMonth(events: TimelineEvent[]): Record<string, TimelineEvent[]> {
  const grouped: Record<string, TimelineEvent[]> = {};
  events.forEach((event) => {
    const monthKey = event.date.substring(0, 7); // YYYY-MM
    if (!grouped[monthKey]) grouped[monthKey] = [];
    grouped[monthKey].push(event);
  });
  return grouped;
}

function countEventsByType(events: TimelineEvent[]): Record<string, number> {
  const counts: Record<string, number> = {};
  events.forEach((event) => {
    counts[event.eventType] = (counts[event.eventType] || 0) + 1;
  });
  return counts;
}

function countEventsByCase(events: TimelineEvent[]): Record<string, number> {
  const counts: Record<string, number> = {};
  events.forEach((event) => {
    counts[event.caseId] = (counts[event.caseId] || 0) + 1;
  });
  return counts;
}

function calculateDaysDifference(startDate: string, endDate: string): number {
  const start = new Date(startDate);
  const end = new Date(endDate);
  return Math.floor((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24));
}

function getMostActiveCaseInfo(eventsByCase: Record<string, number>, allCases: typeof cases): string {
  const [caseId, count] = Object.entries(eventsByCase).sort(([, a], [, b]) => b - a)[0];
  const caseItem = allCases.find((c) => c.id === caseId);
  return `${caseItem?.name} (${count} events)`;
}

function getMostCommonEventType(eventsByType: Record<string, number>): string {
  const [type, count] = Object.entries(eventsByType).sort(([, a], [, b]) => b - a)[0];
  return `${type} (${count} events)`;
}

function calculateLitigationIntensity(events: TimelineEvent[]): string {
  if (events.length === 0) return '0';
  const days = calculateDaysDifference(events[0].date, events[events.length - 1].date);
  const months = Math.ceil(days / 30);
  const intensity = (events.length / months).toFixed(1);
  return intensity;
}

function identifyCriticalPeriod(events: TimelineEvent[]): string {
  // Find the month with the most events
  const monthCounts: Record<string, number> = {};
  events.forEach((event) => {
    const month = event.date.substring(0, 7);
    monthCounts[month] = (monthCounts[month] || 0) + 1;
  });
  const [month, count] = Object.entries(monthCounts).sort(([, a], [, b]) => b - a)[0];
  return `${month} (${count} events)`;
}
