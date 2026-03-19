import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AlertCircle, CheckCircle, Clock, FileText, Gavel, AlertTriangle } from "lucide-react";

export interface TimelineEvent {
  date: string;
  title: string;
  description: string;
  type: "filing" | "hearing" | "violation" | "decision" | "motion" | "evidence";
  severity?: "critical" | "high" | "medium" | "low";
}

const timelineEvents: TimelineEvent[] = [
  {
    date: "2024-12-15",
    title: "Initial Lease Dispute",
    description: "Tenant reports billing discrepancies and unauthorized charges on lease account",
    type: "evidence",
    severity: "high",
  },
  {
    date: "2025-01-10",
    title: "Sewage Leak Reported",
    description: "Environmental hazard discovered - raw sewage discharge on property grounds",
    type: "violation",
    severity: "critical",
  },
  {
    date: "2025-01-15",
    title: "EGLE Violation Notice",
    description: "Michigan EGLE issues violation report for Part 31 environmental code violations",
    type: "filing",
    severity: "critical",
  },
  {
    date: "2025-01-20",
    title: "MDHHS Payment Offset",
    description: "Housing assistance payments begin being offset by landlord claims",
    type: "evidence",
    severity: "high",
  },
  {
    date: "2025-02-01",
    title: "Eviction Notice Filed",
    description: "60th District Court receives eviction filing from Shady Oaks MHP LLC",
    type: "filing",
    severity: "high",
  },
  {
    date: "2025-02-15",
    title: "Tenant Response Filed",
    description: "Verified response filed in 60th District Court with habitability defenses",
    type: "filing",
    severity: "medium",
  },
  {
    date: "2025-03-01",
    title: "Discovery Motion",
    description: "Motion to Compel Discovery filed - requesting entity records and billing documentation",
    type: "motion",
    severity: "medium",
  },
  {
    date: "2025-03-15",
    title: "Eviction Judgment",
    description: "60th District Court enters judgment for plaintiff - eviction order issued",
    type: "decision",
    severity: "critical",
  },
  {
    date: "2025-03-20",
    title: "Emergency TRO Filed",
    description: "Temporary Restraining Order filed in 14th Circuit Court to stay eviction",
    type: "motion",
    severity: "critical",
  },
  {
    date: "2025-04-01",
    title: "Comprehensive Complaint",
    description: "14th Circuit receives detailed complaint with multiple counts including constitutional violations",
    type: "filing",
    severity: "high",
  },
  {
    date: "2025-04-15",
    title: "Exhibit Compilation",
    description: "Complete exhibit set (A-Z) compiled with photographic evidence and documentation",
    type: "evidence",
    severity: "medium",
  },
  {
    date: "2025-05-01",
    title: "Attorney Conflict Identified",
    description: "Piper Legal identified as having dual role - attorney and entity principal",
    type: "evidence",
    severity: "high",
  },
  {
    date: "2025-05-15",
    title: "Neighbor Affidavit",
    description: "Neighbor filing prepared documenting pattern of management misconduct",
    type: "evidence",
    severity: "medium",
  },
  {
    date: "2025-05-27",
    title: "Current Status",
    description: "Case pending in 14th Circuit with comprehensive documentation and exhibits prepared",
    type: "filing",
    severity: "high",
  },
];

const getEventIcon = (type: TimelineEvent["type"]) => {
  switch (type) {
    case "filing":
      return <FileText className="w-5 h-5" />;
    case "hearing":
      return <Gavel className="w-5 h-5" />;
    case "violation":
      return <AlertTriangle className="w-5 h-5" />;
    case "decision":
      return <CheckCircle className="w-5 h-5" />;
    case "motion":
      return <Clock className="w-5 h-5" />;
    case "evidence":
      return <AlertCircle className="w-5 h-5" />;
    default:
      return <Clock className="w-5 h-5" />;
  }
};

const getEventColor = (type: TimelineEvent["type"]) => {
  switch (type) {
    case "filing":
      return "bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-200";
    case "hearing":
      return "bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-200";
    case "violation":
      return "bg-red-100 text-red-700 dark:bg-red-900 dark:text-red-200";
    case "decision":
      return "bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-200";
    case "motion":
      return "bg-yellow-100 text-yellow-700 dark:bg-yellow-900 dark:text-yellow-200";
    case "evidence":
      return "bg-orange-100 text-orange-700 dark:bg-orange-900 dark:text-orange-200";
    default:
      return "bg-gray-100 text-gray-700 dark:bg-gray-900 dark:text-gray-200";
  }
};

const getSeverityBadgeColor = (severity?: string) => {
  switch (severity) {
    case "critical":
      return "bg-destructive text-destructive-foreground";
    case "high":
      return "bg-accent text-accent-foreground";
    case "medium":
      return "bg-secondary text-secondary-foreground";
    case "low":
      return "bg-muted text-muted-foreground";
    default:
      return "bg-muted text-muted-foreground";
  }
};

export function CaseTimeline() {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  };

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Clock className="w-6 h-6 text-accent" />
          Case Timeline
        </CardTitle>
        <CardDescription>
          Chronological progression of key events, filings, and decisions
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative">
          {/* Timeline vertical line */}
          <div className="absolute left-8 top-0 bottom-0 w-1 bg-gradient-to-b from-accent via-accent to-muted"></div>

          {/* Timeline events */}
          <div className="space-y-8">
            {timelineEvents.map((event, index) => (
              <div key={index} className="relative pl-24">
                {/* Timeline dot */}
                <div className="absolute left-0 top-2 w-16 flex items-center justify-center">
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center ${getEventColor(event.type)} border-4 border-background shadow-lg`}>
                    {getEventIcon(event.type)}
                  </div>
                </div>

                {/* Event card */}
                <div className="bg-card border border-border rounded-lg p-4 hover:shadow-md transition-shadow duration-300">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold text-foreground text-lg">{event.title}</h4>
                        {event.severity && (
                          <Badge className={getSeverityBadgeColor(event.severity)} variant="secondary">
                            {event.severity.toUpperCase()}
                          </Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">{event.description}</p>
                      <div className="flex items-center gap-2">
                        <Clock className="w-4 h-4 text-accent" />
                        <span className="text-xs font-medium text-accent">{formatDate(event.date)}</span>
                      </div>
                    </div>
                    <Badge variant="outline" className="text-xs whitespace-nowrap">
                      {event.type.charAt(0).toUpperCase() + event.type.slice(1)}
                    </Badge>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Timeline end marker */}
          <div className="relative pl-24 mt-8">
            <div className="absolute left-0 top-2 w-16 flex items-center justify-center">
              <div className="w-10 h-10 rounded-full flex items-center justify-center bg-primary text-primary-foreground border-4 border-background shadow-lg">
                <CheckCircle className="w-5 h-5" />
              </div>
            </div>
            <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
              <h4 className="font-semibold text-foreground">Current Status</h4>
              <p className="text-sm text-muted-foreground mt-1">
                Case pending in 14th Circuit Court with comprehensive documentation prepared
              </p>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
