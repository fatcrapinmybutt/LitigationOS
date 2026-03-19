import { useState, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cases } from '@/data/cases';
import { Calendar, AlertCircle, FileText, Filter, Clock, Zap } from 'lucide-react';

interface TimelineEvent {
  date: string;
  dateObj: Date;
  event: string;
  caseId: string;
  caseName: string;
  caseColor: string;
  eventType: 'filing' | 'hearing' | 'violation' | 'decision' | 'motion' | 'evidence' | 'other';
  relatedExhibits?: string[];
}

interface PredictedEvent {
  date: string;
  dateObj: Date;
  event: string;
  caseId: string;
  caseName: string;
  caseColor: string;
  eventType: 'discovery' | 'motion_deadline' | 'hearing' | 'appeal' | 'settlement' | 'trial';
  confidence: 'high' | 'medium' | 'low';
  description: string;
}

export function EnhancedMasterTimeline() {
  // State for filtering
  const [selectedCases, setSelectedCases] = useState<Set<string>>(new Set(cases.map((c) => c.id)));
  const [selectedEventTypes, setSelectedEventTypes] = useState<Set<string>>(
    new Set(['filing', 'hearing', 'violation', 'decision', 'motion', 'evidence', 'other'])
  );
  const [dateRangeStart, setDateRangeStart] = useState('2024-11-01');
  const [dateRangeEnd, setDateRangeEnd] = useState('2025-12-31');
  const [showPredicted, setShowPredicted] = useState(true);
  const [showEvidence, setShowEvidence] = useState(true);

  // Consolidate all actual events
  const allActualEvents: TimelineEvent[] = useMemo(() => {
    const events: TimelineEvent[] = [];
    cases.forEach((caseItem) => {
      caseItem.keyDates.forEach((keyDate) => {
        events.push({
          date: keyDate.date,
          dateObj: new Date(keyDate.date),
          event: keyDate.event,
          caseId: caseItem.id,
          caseName: caseItem.name,
          caseColor: caseItem.color,
          eventType: determineEventType(keyDate.event),
          relatedExhibits: getRelatedExhibits(caseItem, keyDate.event),
        });
      });
    });
    return events.sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());
  }, []);

  // Generate predicted events
  const predictedEvents: PredictedEvent[] = useMemo(() => {
    const predictions: PredictedEvent[] = [];
    cases.forEach((caseItem) => {
      const lastDate = new Date(caseItem.keyDates[caseItem.keyDates.length - 1]?.date || new Date());

      // Discovery phase (typically 30-60 days after filing)
      predictions.push({
        date: addDays(lastDate, 45).toISOString().split('T')[0],
        dateObj: addDays(lastDate, 45),
        event: 'Discovery Period Begins',
        caseId: caseItem.id,
        caseName: caseItem.name,
        caseColor: caseItem.color,
        eventType: 'discovery',
        confidence: 'high',
        description: 'Parties exchange documents and information',
      });

      // Motion deadlines (typically 60-90 days after filing)
      predictions.push({
        date: addDays(lastDate, 75).toISOString().split('T')[0],
        dateObj: addDays(lastDate, 75),
        event: 'Motion Deadline',
        caseId: caseItem.id,
        caseName: caseItem.name,
        caseColor: caseItem.color,
        eventType: 'motion_deadline',
        confidence: 'medium',
        description: 'Deadline for dispositive motions (MSJ, MTD)',
      });

      // Hearing/Conference (typically 120-150 days after filing)
      predictions.push({
        date: addDays(lastDate, 135).toISOString().split('T')[0],
        dateObj: addDays(lastDate, 135),
        event: 'Status Conference/Hearing',
        caseId: caseItem.id,
        caseName: caseItem.name,
        caseColor: caseItem.color,
        eventType: 'hearing',
        confidence: 'medium',
        description: 'Court status conference to assess case progress',
      });

      // Settlement/Trial preparation (typically 180-210 days)
      predictions.push({
        date: addDays(lastDate, 195).toISOString().split('T')[0],
        dateObj: addDays(lastDate, 195),
        event: 'Settlement Conference / Trial Prep',
        caseId: caseItem.id,
        caseName: caseItem.name,
        caseColor: caseItem.color,
        eventType: 'settlement',
        confidence: 'low',
        description: 'Settlement discussions or trial preparation begins',
      });

      // Appeal deadline (if applicable)
      predictions.push({
        date: addDays(lastDate, 240).toISOString().split('T')[0],
        dateObj: addDays(lastDate, 240),
        event: 'Potential Appeal Deadline',
        caseId: caseItem.id,
        caseName: caseItem.name,
        caseColor: caseItem.color,
        eventType: 'appeal',
        confidence: 'low',
        description: 'Deadline for filing appeal (if judgment rendered)',
      });
    });
    return predictions.sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());
  }, []);

  // Filter events based on selections
  const filteredActualEvents = useMemo(() => {
    return allActualEvents.filter((event) => {
      const caseMatch = selectedCases.has(event.caseId);
      const typeMatch = selectedEventTypes.has(event.eventType);
      const dateMatch =
        event.dateObj >= new Date(dateRangeStart) && event.dateObj <= new Date(dateRangeEnd);
      return caseMatch && typeMatch && dateMatch;
    });
  }, [allActualEvents, selectedCases, selectedEventTypes, dateRangeStart, dateRangeEnd]);

  const filteredPredictedEvents = useMemo(() => {
    return predictedEvents.filter((event) => {
      const caseMatch = selectedCases.has(event.caseId);
      const dateMatch =
        event.dateObj >= new Date(dateRangeStart) && event.dateObj <= new Date(dateRangeEnd);
      return caseMatch && dateMatch;
    });
  }, [predictedEvents, selectedCases, dateRangeStart, dateRangeEnd]);

  // Combine and sort all events
  const allCombinedEvents = useMemo(() => {
    const combined: (TimelineEvent | PredictedEvent)[] = [
      ...filteredActualEvents,
      ...(showPredicted ? filteredPredictedEvents : []),
    ];
    return combined.sort((a, b) => a.dateObj.getTime() - b.dateObj.getTime());
  }, [filteredActualEvents, filteredPredictedEvents, showPredicted]);

  const toggleCase = (caseId: string) => {
    const newSet = new Set(selectedCases);
    if (newSet.has(caseId)) {
      newSet.delete(caseId);
    } else {
      newSet.add(caseId);
    }
    setSelectedCases(newSet);
  };

  const toggleEventType = (type: string) => {
    const newSet = new Set(selectedEventTypes);
    if (newSet.has(type)) {
      newSet.delete(type);
    } else {
      newSet.add(type);
    }
    setSelectedEventTypes(newSet);
  };

  return (
    <div className="space-y-6">
      {/* Filter Controls */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="w-6 h-6 text-accent" />
            Timeline Filters & Controls
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Case Filter */}
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Filter by Case</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              {cases.map((caseItem) => (
                <label
                  key={caseItem.id}
                  className="flex items-center gap-3 p-3 rounded-lg border border-border hover:bg-secondary/30 cursor-pointer transition-colors"
                >
                  <Checkbox
                    checked={selectedCases.has(caseItem.id)}
                    onCheckedChange={() => toggleCase(caseItem.id) as any}
                  />
                  <div className="flex items-center gap-2 flex-1">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: caseItem.color }}
                    />
                    <span className="text-sm text-foreground">{caseItem.name.split(' v. ')[0]}</span>
                  </div>
                </label>
              ))}
            </div>
          </div>

          {/* Event Type Filter */}
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Filter by Event Type</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2">
              {['filing', 'hearing', 'violation', 'decision', 'motion', 'evidence', 'other'].map(
                (type) => (
                  <label
                    key={type}
                    className="flex items-center gap-2 p-2 rounded border border-border hover:bg-secondary/30 cursor-pointer transition-colors"
                  >
                    <Checkbox
                      checked={selectedEventTypes.has(type)}
                      onCheckedChange={() => toggleEventType(type) as any}
                    />
                    <span className="text-xs text-foreground capitalize">{type}</span>
                  </label>
                )
              )}
            </div>
          </div>

          {/* Date Range Filter */}
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Date Range</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">Start Date</label>
                <input
                  type="date"
                  value={dateRangeStart}
                  onChange={(e) => setDateRangeStart(e.target.value)}
                  className="w-full px-3 py-2 rounded border border-border bg-background text-foreground"
                />
              </div>
              <div>
                <label className="text-sm text-muted-foreground mb-1 block">End Date</label>
                <input
                  type="date"
                  value={dateRangeEnd}
                  onChange={(e) => setDateRangeEnd(e.target.value)}
                  className="w-full px-3 py-2 rounded border border-border bg-background text-foreground"
                />
              </div>
            </div>
          </div>

          {/* Toggle Options */}
          <div className="space-y-3">
            <h3 className="font-semibold text-foreground">Display Options</h3>
            <div className="flex flex-wrap gap-3">
              <label className="flex items-center gap-2 p-3 rounded-lg border border-border hover:bg-secondary/30 cursor-pointer transition-colors">
                <Checkbox checked={showPredicted} onCheckedChange={(checked) => setShowPredicted(checked === true)} />
                <span className="text-sm text-foreground">Show Predicted Events</span>
              </label>
              <label className="flex items-center gap-2 p-3 rounded-lg border border-border hover:bg-secondary/30 cursor-pointer transition-colors">
                <Checkbox checked={showEvidence} onCheckedChange={(checked) => setShowEvidence(checked === true)} />
                <span className="text-sm text-foreground">Show Evidence Links</span>
              </label>
            </div>
          </div>

          {/* Filter Stats */}
          <div className="p-3 bg-accent/10 rounded-lg border border-accent/20">
            <p className="text-sm text-muted-foreground">
              Showing <strong>{filteredActualEvents.length}</strong> actual events
              {showPredicted && <> + <strong>{filteredPredictedEvents.length}</strong> predicted events</>}
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Enhanced Timeline View */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-6 h-6 text-accent" />
            Filtered Timeline
          </CardTitle>
        </CardHeader>
        <CardContent>
          <ScrollArea className="h-[800px] pr-4">
            <div className="space-y-4">
              {allCombinedEvents.length === 0 ? (
                <div className="p-8 text-center text-muted-foreground">
                  No events match your filter criteria. Try adjusting your selections.
                </div>
              ) : (
                allCombinedEvents.map((event, idx) => {
                  const isPredicted = 'confidence' in event;
                  const relatedExhibits = !isPredicted && 'relatedExhibits' in event ? event.relatedExhibits : [];

                  return (
                    <div key={`${event.date}-${idx}`} className="relative pl-8">
                      {/* Timeline line */}
                      <div className="absolute left-0 top-0 bottom-0 w-0.5 bg-gradient-to-b from-accent via-accent/50 to-accent/20" />

                      {/* Timeline dot */}
                      <div
                        className={`absolute left-0 top-2 w-4 h-4 rounded-full border-2 border-background transform -translate-x-1.5 ${
                          isPredicted ? 'opacity-60' : ''
                        }`}
                        style={{ backgroundColor: event.caseColor }}
                      />

                      {/* Event card */}
                      <div
                        className={`p-4 rounded-lg border transition-all ${
                          isPredicted
                            ? 'border-dashed border-muted-foreground/30 bg-secondary/20'
                            : 'border-border hover:shadow-md'
                        }`}
                      >
                        <div className="flex items-start justify-between gap-3 mb-2">
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-1">
                              <p className="font-semibold text-foreground">{event.event}</p>
                              {isPredicted && (
                                <Badge
                                  variant="outline"
                                  className={`text-xs ${
                                    event.confidence === 'high'
                                      ? 'bg-green-50 text-green-700'
                                      : event.confidence === 'medium'
                                        ? 'bg-yellow-50 text-yellow-700'
                                        : 'bg-orange-50 text-orange-700'
                                  }`}
                                >
                                  {event.confidence} confidence
                                </Badge>
                              )}
                            </div>
                            <p className="text-sm text-muted-foreground">{event.caseName}</p>
                            {isPredicted && 'description' in event && (
                              <p className="text-xs text-muted-foreground mt-1 italic">{event.description}</p>
                            )}
                          </div>
                          <div className="text-right flex-shrink-0">
                            <p className="font-bold text-foreground">{event.date}</p>
                            <Badge variant="outline" className="text-xs mt-1">
                              {isPredicted ? 'predicted' : event.eventType}
                            </Badge>
                          </div>
                        </div>

                        {/* Evidence Links */}
                        {showEvidence && relatedExhibits && relatedExhibits.length > 0 && (
                          <div className="mt-3 pt-3 border-t border-border/50">
                            <p className="text-xs font-semibold text-muted-foreground mb-2 flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              Related Exhibits
                            </p>
                            <div className="flex flex-wrap gap-1">
                              {relatedExhibits.map((exhibit) => (
                                <Badge key={exhibit} variant="secondary" className="text-xs">
                                  {exhibit}
                                </Badge>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Predicted Event Icon */}
                        {isPredicted && (
                          <div className="mt-3 flex items-center gap-2 text-xs text-muted-foreground">
                            <Zap className="w-3 h-3" />
                            <span>Predicted based on typical litigation progression</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </ScrollArea>
        </CardContent>
      </Card>

      {/* Litigation Roadmap */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="w-6 h-6 text-accent" />
            Anticipated Litigation Roadmap
          </CardTitle>
          <CardDescription>
            Projected timeline based on typical civil litigation progression
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {cases.map((caseItem) => {
              const caseEvents = allActualEvents.filter((e) => e.caseId === caseItem.id);
              const lastDate = caseEvents[caseEvents.length - 1]?.dateObj || new Date();

              return (
                <div key={caseItem.id} className="p-4 rounded-lg border border-border">
                  <h3 className="font-semibold text-foreground mb-3 flex items-center gap-2">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: caseItem.color }}
                    />
                    {caseItem.name}
                  </h3>

                  <div className="space-y-2 text-sm">
                    <div className="flex items-start gap-3">
                      <span className="text-muted-foreground min-w-fit">Current:</span>
                      <span className="text-foreground">{lastDate.toISOString().split('T')[0]}</span>
                    </div>
                    <div className="flex items-start gap-3">
                      <span className="text-muted-foreground min-w-fit">Discovery:</span>
                      <span className="text-foreground">
                        {addDays(lastDate, 45).toISOString().split('T')[0]} (est. 45 days)
                      </span>
                    </div>
                    <div className="flex items-start gap-3">
                      <span className="text-muted-foreground min-w-fit">Motion Deadline:</span>
                      <span className="text-foreground">
                        {addDays(lastDate, 75).toISOString().split('T')[0]} (est. 75 days)
                      </span>
                    </div>
                    <div className="flex items-start gap-3">
                      <span className="text-muted-foreground min-w-fit">Hearing/Conference:</span>
                      <span className="text-foreground">
                        {addDays(lastDate, 135).toISOString().split('T')[0]} (est. 135 days)
                      </span>
                    </div>
                    <div className="flex items-start gap-3">
                      <span className="text-muted-foreground min-w-fit">Settlement/Trial:</span>
                      <span className="text-foreground">
                        {addDays(lastDate, 195).toISOString().split('T')[0]} (est. 195 days)
                      </span>
                    </div>
                  </div>
                </div>
              );
            })}
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

function getRelatedExhibits(caseItem: any, eventDescription: string): string[] {
  const exhibits: string[] = [];
  const lowerEvent = eventDescription.toLowerCase();

  // Map event descriptions to related exhibits
  if (lowerEvent.includes('sewage') || lowerEvent.includes('leak')) {
    exhibits.push('C: Sewage Photos', 'D: EGLE Report');
  }
  if (lowerEvent.includes('rent') || lowerEvent.includes('billing')) {
    exhibits.push('B: Billing Statements', 'F: Rent Hike');
  }
  if (lowerEvent.includes('egle') || lowerEvent.includes('violation')) {
    exhibits.push('D: EGLE Report');
  }
  if (lowerEvent.includes('email') || lowerEvent.includes('communication')) {
    exhibits.push('E: Email Logs', 'I: Email Exchanges');
  }
  if (lowerEvent.includes('court') || lowerEvent.includes('judgment')) {
    exhibits.push('J: Court Order');
  }
  if (lowerEvent.includes('eviction')) {
    exhibits.push('J: Court Order');
  }

  return Array.from(new Set(exhibits));
}

function addDays(date: Date, days: number): Date {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
}
