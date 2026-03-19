import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  caseStrengthAnalyses,
  getCaseStrengthAnalysis,
  getStrengthColor,
  getStrengthLabel,
} from '@/data/case_strength_model';
import { multiCaseTracks } from '@/data/multi_case_data';
import { TrendingUp, AlertTriangle, CheckCircle, Target, Zap } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar } from 'recharts';

export function CaseStrengthAnalyzer() {
  const [selectedCaseId, setSelectedCaseId] = useState<string>('case-2024-1507-dc');

  const selectedAnalysis = getCaseStrengthAnalysis(selectedCaseId);
  const selectedCaseInfo = multiCaseTracks.find((c) => c.id === selectedCaseId);

  if (!selectedAnalysis || !selectedCaseInfo) {
    return <div>Case not found</div>;
  }

  // Prepare radar chart data
  const radarData = [
    {
      category: 'Legal Elements',
      value: selectedAnalysis.elementScore,
      fullMark: 100,
    },
    {
      category: 'Precedent',
      value: selectedAnalysis.precedentScore,
      fullMark: 100,
    },
    {
      category: 'Jurisdiction',
      value: selectedAnalysis.jurisdictionScore,
      fullMark: 100,
    },
  ];

  // Prepare element breakdown chart
  const elementChartData = selectedAnalysis.elements.map((el) => ({
    name: el.name,
    score:
      el.status === 'strong'
        ? 100
        : el.status === 'moderate'
          ? 60
          : el.status === 'weak'
            ? 30
            : 0,
  }));

  // Prepare comparison chart
  const comparisonData = caseStrengthAnalyses.map((analysis) => ({
    case: multiCaseTracks.find((c) => c.id === analysis.caseId)?.caseNumber || 'Unknown',
    strength: analysis.overallStrength,
  }));

  return (
    <div className="space-y-6">
      {/* Case Selector */}
      <Card>
        <CardHeader>
          <CardTitle>Select Case for Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3">
            {caseStrengthAnalyses.map((analysis) => {
              const caseInfo = multiCaseTracks.find((c) => c.id === analysis.caseId);
              const isSelected = selectedCaseId === analysis.caseId;

              return (
                <button
                  key={analysis.caseId}
                  onClick={() => setSelectedCaseId(analysis.caseId)}
                  className={`p-4 rounded-lg border-2 transition-all text-left ${
                    isSelected
                      ? 'border-accent bg-accent/10'
                      : 'border-border hover:border-accent/50'
                  }`}
                >
                  <p className="font-semibold text-foreground text-sm">{caseInfo?.caseNumber}</p>
                  <div className="mt-2 flex items-center gap-2">
                    <div className="flex-1 h-2 bg-secondary rounded-full overflow-hidden">
                      <div
                        className="h-full transition-all"
                        style={{
                          width: `${analysis.overallStrength}%`,
                          backgroundColor: getStrengthColor(analysis.overallStrength),
                        }}
                      />
                    </div>
                    <p className="text-xs font-bold text-foreground">{analysis.overallStrength}%</p>
                  </div>
                  <p className="text-xs text-muted-foreground mt-1">{getStrengthLabel(analysis.overallStrength)}</p>
                </button>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* Main Strength Score */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              <TrendingUp className="w-6 h-6 text-accent" />
              Case Strength Analysis
            </span>
            <Badge style={{ backgroundColor: getStrengthColor(selectedAnalysis.overallStrength) }}>
              {getStrengthLabel(selectedAnalysis.overallStrength)}
            </Badge>
          </CardTitle>
          <CardDescription>{selectedAnalysis.caseName}</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Overall Strength Gauge */}
          <div className="flex items-center gap-8">
            <div className="flex-1">
              <div className="relative w-48 h-48 mx-auto">
                {/* Circular gauge */}
                <svg className="w-full h-full" viewBox="0 0 200 200">
                  {/* Background circle */}
                  <circle cx="100" cy="100" r="90" fill="none" stroke="#e5e7eb" strokeWidth="20" />
                  {/* Progress circle */}
                  <circle
                    cx="100"
                    cy="100"
                    r="90"
                    fill="none"
                    stroke={getStrengthColor(selectedAnalysis.overallStrength)}
                    strokeWidth="20"
                    strokeDasharray={`${(selectedAnalysis.overallStrength / 100) * 565.48} 565.48`}
                    strokeLinecap="round"
                    style={{ transform: 'rotate(-90deg)', transformOrigin: '100px 100px', transition: 'all 0.3s' }}
                  />
                  {/* Center text */}
                  <text x="100" y="95" textAnchor="middle" className="text-4xl font-bold fill-foreground">
                    {selectedAnalysis.overallStrength}%
                  </text>
                  <text x="100" y="115" textAnchor="middle" className="text-sm fill-muted-foreground">
                    Strength
                  </text>
                </svg>
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="flex-1 space-y-4">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="font-semibold text-foreground">Legal Elements</p>
                  <p className="text-sm font-bold text-foreground">{selectedAnalysis.elementScore}%</p>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all"
                    style={{ width: `${selectedAnalysis.elementScore}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="font-semibold text-foreground">Precedent Analysis</p>
                  <p className="text-sm font-bold text-foreground">{selectedAnalysis.precedentScore}%</p>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-purple-500 transition-all"
                    style={{ width: `${selectedAnalysis.precedentScore}%` }}
                  />
                </div>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <p className="font-semibold text-foreground">Jurisdiction Favorability</p>
                  <p className="text-sm font-bold text-foreground">{selectedAnalysis.jurisdictionScore}%</p>
                </div>
                <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                  <div
                    className="h-full bg-green-500 transition-all"
                    style={{ width: `${selectedAnalysis.jurisdictionScore}%` }}
                  />
                </div>
              </div>

              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">
                  <span className="font-semibold">Confidence Level:</span> {selectedAnalysis.confidence}%
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Tabs for detailed analysis */}
      <Tabs defaultValue="overview" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="elements">Elements</TabsTrigger>
          <TabsTrigger value="precedents">Precedents</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
          <TabsTrigger value="comparison">Comparison</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Strengths */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-green-600">
                  <CheckCircle className="w-5 h-5" />
                  Strengths
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {selectedAnalysis.strengths.map((strength, idx) => (
                    <li key={idx} className="flex gap-2 text-sm">
                      <span className="text-green-600 font-bold">•</span>
                      <span className="text-foreground">{strength}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>

            {/* Weaknesses */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-orange-600">
                  <AlertTriangle className="w-5 h-5" />
                  Weaknesses
                </CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="space-y-2">
                  {selectedAnalysis.weaknesses.map((weakness, idx) => (
                    <li key={idx} className="flex gap-2 text-sm">
                      <span className="text-orange-600 font-bold">•</span>
                      <span className="text-foreground">{weakness}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          </div>

          {/* Risk Factors */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-red-600">
                <Zap className="w-5 h-5" />
                Risk Factors
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {selectedAnalysis.riskFactors.map((risk, idx) => (
                  <li key={idx} className="flex gap-2 text-sm">
                    <span className="text-red-600 font-bold">⚠</span>
                    <span className="text-foreground">{risk}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>

          {/* Recommendations */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-blue-600">
                <Target className="w-5 h-5" />
                Recommendations
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {selectedAnalysis.recommendations.map((rec, idx) => (
                  <li key={idx} className="flex gap-2 text-sm">
                    <span className="text-blue-600 font-bold">→</span>
                    <span className="text-foreground">{rec}</span>
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Elements Tab */}
        <TabsContent value="elements" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Legal Elements Analysis</CardTitle>
              <CardDescription>Status of required legal elements for case success</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={elementChartData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="score" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>

              <ScrollArea className="h-[400px]">
                <div className="space-y-3 pr-4">
                  {selectedAnalysis.elements.map((element) => (
                    <div key={element.id} className="p-3 rounded-lg border border-border">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex-1">
                          <p className="font-semibold text-foreground text-sm">{element.name}</p>
                          <p className="text-xs text-muted-foreground mt-1">{element.description}</p>
                        </div>
                        <Badge
                          className={
                            element.status === 'strong'
                              ? 'bg-green-100 text-green-800'
                              : element.status === 'moderate'
                                ? 'bg-yellow-100 text-yellow-800'
                                : element.status === 'weak'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-red-100 text-red-800'
                          }
                        >
                          {element.status}
                        </Badge>
                      </div>

                      {element.evidence.length > 0 && (
                        <div className="mt-2 pt-2 border-t border-border/50">
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Evidence:</p>
                          <ul className="text-xs text-foreground space-y-1">
                            {element.evidence.map((ev, idx) => (
                              <li key={idx} className="flex gap-1">
                                <span>•</span>
                                <span>{ev}</span>
                              </li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Precedents Tab */}
        <TabsContent value="precedents" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Similar Precedent Cases</CardTitle>
              <CardDescription>Historical cases with similar facts and legal issues</CardDescription>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3 pr-4">
                  {selectedAnalysis.precedents.map((precedent) => (
                    <div key={precedent.id} className="p-4 rounded-lg border border-border">
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex-1">
                          <p className="font-semibold text-foreground">{precedent.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {precedent.court} ({precedent.year})
                          </p>
                        </div>
                        <Badge
                          className={
                            precedent.outcome === 'plaintiff-win'
                              ? 'bg-green-100 text-green-800'
                              : precedent.outcome === 'defendant-win'
                                ? 'bg-red-100 text-red-800'
                                : 'bg-blue-100 text-blue-800'
                          }
                        >
                          {precedent.outcome === 'plaintiff-win'
                            ? 'Plaintiff Win'
                            : precedent.outcome === 'defendant-win'
                              ? 'Defendant Win'
                              : 'Settlement'}
                        </Badge>
                      </div>

                      <div className="mt-3 pt-3 border-t border-border/50 space-y-2">
                        <div>
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Similarity:</p>
                          <div className="w-full h-2 bg-secondary rounded-full overflow-hidden">
                            <div
                              className="h-full bg-blue-500"
                              style={{ width: `${precedent.similarity * 100}%` }}
                            />
                          </div>
                          <p className="text-xs text-muted-foreground mt-1">{Math.round(precedent.similarity * 100)}% match</p>
                        </div>

                        <div>
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Key Facts:</p>
                          <ul className="text-xs text-foreground space-y-1">
                            {precedent.keyFacts.map((fact, idx) => (
                              <li key={idx} className="flex gap-1">
                                <span>•</span>
                                <span>{fact}</span>
                              </li>
                            ))}
                          </ul>
                        </div>

                        <div>
                          <p className="text-xs font-semibold text-muted-foreground mb-1">Relevant Law:</p>
                          <p className="text-xs text-foreground">{precedent.relevantLaw}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Scoring Analysis</CardTitle>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={400}>
                <RadarChart data={radarData}>
                  <PolarGrid />
                  <PolarAngleAxis dataKey="category" />
                  <PolarRadiusAxis angle={90} domain={[0, 100]} />
                  <Radar name="Score" dataKey="value" stroke="#8884d8" fill="#8884d8" fillOpacity={0.6} />
                </RadarChart>
              </ResponsiveContainer>

              <div className="mt-6 space-y-4">
                <div>
                  <p className="font-semibold text-foreground mb-2">Scoring Methodology:</p>
                  <ul className="text-sm text-muted-foreground space-y-2">
                    <li>• <span className="font-semibold">Legal Elements (50%)</span>: Analysis of required elements for case success</li>
                    <li>• <span className="font-semibold">Precedent Analysis (30%)</span>: Comparison with similar historical cases</li>
                    <li>• <span className="font-semibold">Jurisdiction Favorability (20%)</span>: Local court trends and statutory environment</li>
                  </ul>
                </div>

                <div className="pt-4 border-t border-border">
                  <p className="font-semibold text-foreground mb-2">Overall Assessment:</p>
                  <p className="text-sm text-foreground">
                    This case has a <span className="font-bold">{getStrengthLabel(selectedAnalysis.overallStrength).toLowerCase()}</span> probability of success based on current evidence and legal analysis. The confidence level of {selectedAnalysis.confidence}% indicates the reliability of this assessment.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comparison Tab */}
        <TabsContent value="comparison" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Case Strength Comparison</CardTitle>
              <CardDescription>Relative strength across all cases</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={comparisonData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="case" />
                  <YAxis domain={[0, 100]} />
                  <Tooltip />
                  <Bar dataKey="strength" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>

              <div className="mt-6 space-y-3">
                {comparisonData.map((item, idx) => {
                  const analysis = caseStrengthAnalyses[idx];
                  return (
                    <div key={item.case} className="flex items-center justify-between p-3 rounded-lg border border-border">
                      <p className="font-semibold text-foreground">{item.case}</p>
                      <div className="flex items-center gap-3">
                        <div className="w-32 h-2 bg-secondary rounded-full overflow-hidden">
                          <div
                            className="h-full transition-all"
                            style={{
                              width: `${item.strength}%`,
                              backgroundColor: getStrengthColor(item.strength),
                            }}
                          />
                        </div>
                        <p className="text-sm font-bold text-foreground w-12 text-right">{item.strength}%</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
