import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cases, CaseProfile } from '@/data/cases';
import { Scale, FileText, Users, Calendar } from 'lucide-react';

interface CaseSelectorProps {
  selectedCaseId: string;
  onCaseSelect: (caseId: string) => void;
}

export function CaseSelector({ selectedCaseId, onCaseSelect }: CaseSelectorProps) {
  const selectedCase = cases.find((c) => c.id === selectedCaseId);
  const [showDetails, setShowDetails] = useState(false);

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Scale className="w-6 h-6 text-accent" />
          Case Selection
        </CardTitle>
        <CardDescription>
          Switch between {cases.length} related litigation matters
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Case Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {cases.map((caseItem) => (
            <button
              key={caseItem.id}
              onClick={() => {
                onCaseSelect(caseItem.id);
                setShowDetails(true);
              }}
              className={`p-4 rounded-lg border-2 text-left transition-all ${
                selectedCaseId === caseItem.id
                  ? 'border-accent bg-accent/10'
                  : 'border-border hover:border-accent/50 hover:bg-secondary/30'
              }`}
            >
              <div className="flex items-start justify-between gap-2 mb-2">
                <h3 className="font-semibold text-foreground text-sm">{caseItem.name}</h3>
                <div
                  className="w-3 h-3 rounded-full flex-shrink-0 mt-1"
                  style={{ backgroundColor: caseItem.color }}
                />
              </div>
              <p className="text-xs text-muted-foreground mb-2">{caseItem.caseNumber}</p>
              <div className="flex gap-2 flex-wrap">
                <Badge variant="outline" className="text-xs">
                  {caseItem.status.split(' - ')[1] || caseItem.status}
                </Badge>
              </div>
            </button>
          ))}
        </div>

        {/* Selected Case Details */}
        {selectedCase && (
          <div className="space-y-4 pt-4 border-t border-border">
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold text-foreground">{selectedCase.name}</h2>
                <p className="text-sm text-muted-foreground mt-1">{selectedCase.caseNumber}</p>
              </div>
              <Badge
                className="text-white"
                style={{ backgroundColor: selectedCase.color }}
              >
                {selectedCase.status.split(' - ')[0]}
              </Badge>
            </div>

            {/* Case Info Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="p-3 rounded-lg bg-secondary/30 border border-border">
                <p className="text-xs text-muted-foreground mb-1">Court</p>
                <p className="text-sm font-medium text-foreground">{selectedCase.court.split(',')[0]}</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/30 border border-border">
                <p className="text-xs text-muted-foreground mb-1">Judge</p>
                <p className="text-sm font-medium text-foreground">{selectedCase.judge.replace('Hon. ', '')}</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/30 border border-border">
                <p className="text-xs text-muted-foreground mb-1">Filed</p>
                <p className="text-sm font-medium text-foreground">{selectedCase.filingDate}</p>
              </div>
              <div className="p-3 rounded-lg bg-secondary/30 border border-border">
                <p className="text-xs text-muted-foreground mb-1">Status</p>
                <p className="text-sm font-medium text-foreground">{selectedCase.status.split(' - ')[0]}</p>
              </div>
            </div>

            {/* Parties */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Users className="w-4 h-4 text-accent" />
                Parties
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
                  <p className="text-xs text-muted-foreground mb-1">Plaintiff</p>
                  <p className="font-medium text-foreground text-sm">{selectedCase.plaintiff}</p>
                </div>
                <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
                  <p className="text-xs text-muted-foreground mb-1">Defendants ({selectedCase.defendants.length})</p>
                  <div className="space-y-1">
                    {selectedCase.defendants.map((defendant) => (
                      <p key={defendant} className="text-sm text-foreground">
                        {defendant}
                      </p>
                    ))}
                  </div>
                </div>
              </div>
            </div>

            {/* Legal Issues */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <FileText className="w-4 h-4 text-accent" />
                Legal Issues ({selectedCase.legalIssues.length})
              </h3>
              <ul className="space-y-1">
                {selectedCase.legalIssues.map((issue, idx) => (
                  <li key={idx} className="text-sm text-muted-foreground flex gap-2">
                    <span className="text-accent">•</span>
                    <span>{issue}</span>
                  </li>
                ))}
              </ul>
            </div>

            {/* Key Dates */}
            <div className="space-y-2">
              <h3 className="text-sm font-semibold text-foreground flex items-center gap-2">
                <Calendar className="w-4 h-4 text-accent" />
                Key Dates
              </h3>
              <div className="space-y-2">
                {selectedCase.keyDates.map((item, idx) => (
                  <div key={idx} className="flex gap-3 text-sm">
                    <span className="text-muted-foreground min-w-fit font-medium">{item.date}</span>
                    <span className="text-foreground">{item.event}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Quick Stats */}
        <div className="grid grid-cols-4 gap-2 p-3 bg-secondary/30 rounded-lg border border-border">
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Total Cases</p>
            <p className="text-lg font-bold text-foreground">{cases.length}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Active</p>
            <p className="text-lg font-bold text-foreground">{cases.filter((c) => c.status.includes('Active')).length}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Courts</p>
            <p className="text-lg font-bold text-foreground">{new Set(cases.map((c) => c.court)).size}</p>
          </div>
          <div className="text-center">
            <p className="text-xs text-muted-foreground">Judges</p>
            <p className="text-lg font-bold text-foreground">{new Set(cases.map((c) => c.judge)).size}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
