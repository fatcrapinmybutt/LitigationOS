import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { FileText, Scale, Building2, AlertCircle, TrendingUp, Users, Gavel, FileCheck } from "lucide-react";
import { CaseTimeline } from "@/components/CaseTimeline";
import { LegalNetworkGraph } from "@/components/LegalNetworkGraph";
import { LegalKnowledgeBase } from "@/components/LegalKnowledgeBase";
import { LegalDependencyMap } from "@/components/LegalDependencyMap";
import { CitationGenerator } from "@/components/CitationGenerator";
import { BriefTemplateGenerator } from "@/components/BriefTemplateGenerator";
import { CaseSelector } from "@/components/CaseSelector";
import { CaseComparison } from "@/components/CaseComparison";
import { EnhancedMasterTimeline } from '@/components/EnhancedMasterTimeline';
import { CaseStrengthAnalyzer } from '@/components/CaseStrengthAnalyzer';
import { FamilyLawCaseTracker } from '@/components/FamilyLawCaseTracker';
import { JudicialDisqualificationBuilder } from '@/components/JudicialDisqualificationBuilder';
import { MultiCaseTracker } from "@/components/MultiCaseTracker";
import { useState } from "react";

export default function Home() {
  const [selectedCaseId, setSelectedCaseId] = useState('pigors-shady-oaks');

  // Data from the analysis
  const keyStats = [
    { label: "Total File Size", value: "9.98 MB", icon: FileText, color: "text-chart-1" },
    { label: "Exhibits", value: "22", icon: FileCheck, color: "text-chart-2" },
    { label: "Court Mentions", value: "3,899", icon: Gavel, color: "text-chart-3" },
    { label: "Motion References", value: "2,873", icon: Scale, color: "text-chart-4" },
  ];

  const termFrequency = [
    { term: "Court", count: 3899 },
    { term: "Exhibit", count: 3529 },
    { term: "Motion", count: 2873 },
    { term: "Plaintiff", count: 1715 },
    { term: "Lease", count: 1626 },
    { term: "Defendant", count: 1112 },
    { term: "Eviction", count: 674 },
  ];

  const exhibits = [
    { letter: "A", desc: "Sewage Leak Email - Include Statement on HOA vs. Shady Oaks suit" },
    { letter: "B", desc: "Withheld Items Screenshot - CONTEMPT filing related evidence" },
    { letter: "C", desc: "Easter Refusal PDF - Timeline Chart evidence" },
    { letter: "D", desc: "Sewage photographs - Unanswered emails - Legal aid documentation" },
    { letter: "E", desc: "Water shutoff with child home - Entity concealment evidence" },
    { letter: "F", desc: "Entity transition evidence - Facebook post showing retaliation" },
    { letter: "G", desc: "Photographs of Sewage Conditions.pdf - Confirmed evidence" },
    { letter: "H", desc: "may272025SHADYOAKSPAGES3-4.pdf - rent claim mismatches" },
    { letter: "I", desc: "Ordered list of key dates and events extracted from documents" },
    { letter: "J", desc: "MAY272025SHADYOAKSpt-3EXHIBITB.pdf - timeline corroborates" },
  ];

  const legalIssues = [
    { category: "Landlord-Tenant Dispute", severity: "high", items: ["Eviction proceedings", "Rent payment disputes", "MDHHS payment offsets"] },
    { category: "Housing Habitability", severity: "critical", items: ["Sewage leak", "EGLE violations", "Health hazards"] },
    { category: "Procedural Issues", severity: "high", items: ["Due process violations", "Improper service", "Jurisdictional challenges"] },
    { category: "Corporate Entity Issues", severity: "medium", items: ["Multiple entities", "Veil piercing", "Attorney conflicts"] },
    { category: "Retaliation Claims", severity: "high", items: ["Retaliatory eviction", "Lease coercion", "Management harassment"] },
  ];

  const caseDistribution = [
    { name: "Court References", value: 3899, color: "#d4af37" },
    { name: "Exhibits", value: 3529, color: "#2c4a7c" },
    { name: "Motions", value: 2873, color: "#1e3a5f" },
    { name: "Parties", value: 2827, color: "#4a7ba7" },
  ];

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case "critical": return "bg-destructive text-destructive-foreground";
      case "high": return "bg-accent text-accent-foreground";
      case "medium": return "bg-secondary text-secondary-foreground";
      default: return "bg-muted text-muted-foreground";
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b border-border bg-card/50 backdrop-blur-sm sticky top-0 z-50">
        <div className="container py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-4xl font-bold tracking-tight text-foreground mb-2">
                Eternal Bloom MAX
              </h1>
              <p className="text-muted-foreground text-lg">Legal Case Analysis Dashboard</p>
            </div>
            <Badge variant="outline" className="text-lg px-4 py-2 border-accent text-accent-foreground">
              <Scale className="w-4 h-4 mr-2" />
              Active Case
            </Badge>
          </div>
        </div>
      </header>

      <main className="container py-8">
        {/* Key Statistics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {keyStats.map((stat, index) => (
            <Card key={index} className="hover:shadow-lg transition-shadow duration-300">
              <CardHeader className="flex flex-row items-center justify-between pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  {stat.label}
                </CardTitle>
                <stat.icon className={`w-5 h-5 ${stat.color}`} />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold text-foreground">{stat.value}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Main Content Tabs */}
        <Tabs defaultValue="cases" className="space-y-6">
          <TabsList className="grid w-full grid-cols-9">
            <TabsTrigger value="multi-case">Multi-Case</TabsTrigger>
            <TabsTrigger value="cases">Cases</TabsTrigger>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="master-timeline">Master Timeline</TabsTrigger>
            <TabsTrigger value="timeline">Timeline</TabsTrigger>
            <TabsTrigger value="framework">Framework</TabsTrigger>
            <TabsTrigger value="citations">Citations</TabsTrigger>
            <TabsTrigger value="briefs">Briefs</TabsTrigger>
            <TabsTrigger value="strength">Strength</TabsTrigger>
            <TabsTrigger value="family-law">Family Law</TabsTrigger>
            <TabsTrigger value="disqualification">Disqualification</TabsTrigger>
          </TabsList>

          {/* Multi-Case Tracker Tab */}
          <TabsContent value="multi-cases" className="space-y-6">
            <MultiCaseTracker />
          </TabsContent>

          {/* Cases Tab */}
          <TabsContent value="cases" className="space-y-6">
            <CaseSelector selectedCaseId={selectedCaseId} onCaseSelect={setSelectedCaseId} />
            <CaseComparison />
          </TabsContent>

          {/* Master Timeline Tab */}
          <TabsContent value="master-timeline" className="space-y-6">
            <EnhancedMasterTimeline />
          </TabsContent>

          {/* Timeline Tab */}
          <TabsContent value="timeline" className="space-y-6">
            <CaseTimeline />
          </TabsContent>

          {/* Legal Framework Tab */}
          <TabsContent value="legal-framework" className="space-y-6">
            <LegalDependencyMap />
          </TabsContent>

          {/* Citations Tab */}
          <TabsContent value="citations" className="space-y-6">
            <CitationGenerator />
          </TabsContent>

          {/* Briefs Tab */}
          <TabsContent value="briefs" className="space-y-6">
            <BriefTemplateGenerator />
          </TabsContent>

          {/* Case Strength Tab */}
          <TabsContent value="strength" className="space-y-6">
            <CaseStrengthAnalyzer />
          </TabsContent>

          {/* Family Law Cases Tab */}
          <TabsContent value="family-law" className="space-y-6">
            <FamilyLawCaseTracker />
          </TabsContent>

          {/* Judicial Disqualification Tab */}
          <TabsContent value="disqualification" className="space-y-6">
            <JudicialDisqualificationBuilder />
          </TabsContent>

          {/* Overview Tab */}
          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Term Frequency Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Key Term Frequency</CardTitle>
                  <CardDescription>Most referenced legal terms in the case documentation</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={termFrequency}>
                      <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                      <XAxis dataKey="term" stroke="hsl(var(--muted-foreground))" />
                      <YAxis stroke="hsl(var(--muted-foreground))" />
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))', 
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '0.5rem'
                        }} 
                      />
                      <Bar dataKey="count" fill="hsl(var(--chart-1))" radius={[8, 8, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>

              {/* Case Distribution Pie Chart */}
              <Card>
                <CardHeader>
                  <CardTitle>Case Component Distribution</CardTitle>
                  <CardDescription>Breakdown of document references by category</CardDescription>
                </CardHeader>
                <CardContent>
                  <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                      <Pie
                        data={caseDistribution}
                        cx="50%"
                        cy="50%"
                        labelLine={false}
                        label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                        outerRadius={80}
                        fill="#8884d8"
                        dataKey="value"
                      >
                        {caseDistribution.map((entry, index) => (
                          <Cell key={`cell-${index}`} fill={entry.color} />
                        ))}
                      </Pie>
                      <Tooltip 
                        contentStyle={{ 
                          backgroundColor: 'hsl(var(--card))', 
                          border: '1px solid hsl(var(--border))',
                          borderRadius: '0.5rem'
                        }} 
                      />
                    </PieChart>
                  </ResponsiveContainer>
                </CardContent>
              </Card>
            </div>

            {/* Executive Summary */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <FileText className="w-5 h-5 text-accent" />
                  Executive Summary
                </CardTitle>
              </CardHeader>
              <CardContent className="prose prose-sm max-w-none">
                <p className="text-foreground leading-relaxed">
                  This document represents an extensive <strong>legal case file</strong> exported from a ChatGPT conversation. 
                  The content focuses on a <strong>landlord-tenant dispute</strong> involving eviction proceedings, housing conditions 
                  violations, and potential legal misconduct. The case involves multiple parties, exhibits, and court filings across 
                  Michigan's 60th District Court and 14th Circuit Court.
                </p>
                <p className="text-foreground leading-relaxed mt-4">
                  The case involves substantial evidentiary support across <strong>22 exhibits</strong> and addresses multiple legal 
                  theories spanning contract law, property law, environmental law, and civil procedure. Key issues include sewage leaks, 
                  EGLE violations, billing disputes, and alleged retaliatory eviction practices.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Knowledge Base Tab - Hidden but still available */}
          <TabsContent value="knowledge" className="space-y-6" key="knowledge" style={{ display: 'none' }}>
            <LegalKnowledgeBase />
          </TabsContent>

          {/* Exhibits Tab - Hidden but still available */}
          <TabsContent value="exhibits" className="space-y-6" key="exhibits" style={{ display: 'none' }}>
            <Card>
              <CardHeader>
                <CardTitle>Exhibit Catalog</CardTitle>
                <CardDescription>Complete list of evidentiary exhibits referenced in the case</CardDescription>
              </CardHeader>
              <CardContent>
                <ScrollArea className="h-[600px] pr-4">
                  <div className="space-y-4">
                    {exhibits.map((exhibit) => (
                      <div key={exhibit.letter} className="flex gap-4 p-4 rounded-lg border border-border hover:bg-muted/50 transition-colors">
                        <div className="flex-shrink-0">
                          <div className="w-12 h-12 rounded-full bg-accent flex items-center justify-center">
                            <span className="text-xl font-bold text-accent-foreground">{exhibit.letter}</span>
                          </div>
                        </div>
                        <div className="flex-1">
                          <h4 className="font-semibold text-foreground mb-1">Exhibit {exhibit.letter}</h4>
                          <p className="text-sm text-muted-foreground">{exhibit.desc}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </ScrollArea>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Analysis Tab - Hidden but still available */}
          <TabsContent value="analysis" className="space-y-6" key="analysis">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="w-5 h-5 text-destructive" />
                  Key Legal Issues Identified
                </CardTitle>
                <CardDescription>Critical legal themes and patterns discovered in the case documentation</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {legalIssues.map((issue, index) => (
                    <div key={index}>
                      <div className="flex items-center justify-between mb-3">
                        <h4 className="font-semibold text-lg text-foreground">{issue.category}</h4>
                        <Badge className={getSeverityColor(issue.severity)}>
                          {issue.severity.toUpperCase()}
                        </Badge>
                      </div>
                      <ul className="space-y-2 ml-4">
                        {issue.items.map((item, idx) => (
                          <li key={idx} className="flex items-start gap-2 text-muted-foreground">
                            <span className="text-accent mt-1">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                      {index < legalIssues.length - 1 && <Separator className="mt-6" />}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          {/* Parties Tab - Hidden but still available */}
          <TabsContent value="parties" className="space-y-6" key="parties">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Plaintiff */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Building2 className="w-5 h-5 text-chart-2" />
                    Plaintiff/Landlord
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">Shady Oaks MHP LLC</h4>
                    <p className="text-sm text-muted-foreground">1977 Whitehall Road, Muskegon, MI 49445</p>
                  </div>
                  <Separator />
                  <div>
                    <h5 className="font-medium text-foreground mb-2">Related Entities:</h5>
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      <li>• Homes of America</li>
                      <li>• HOA MI Retail Homes LLC</li>
                    </ul>
                  </div>
                </CardContent>
              </Card>

              {/* Defendant */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Users className="w-5 h-5 text-chart-3" />
                    Defendant/Tenant
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <h4 className="font-semibold text-foreground mb-2">Individual Resident (Pigors)</h4>
                    <p className="text-sm text-muted-foreground">Mobile home lot rental arrangement</p>
                  </div>
                  <Separator />
                  <div>
                    <h5 className="font-medium text-foreground mb-2">Assistance:</h5>
                    <p className="text-sm text-muted-foreground">Receiving MDHHS housing assistance</p>
                  </div>
                </CardContent>
              </Card>

              {/* Legal Representation */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Gavel className="w-5 h-5 text-accent" />
                    Legal Representation
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h4 className="font-semibold text-foreground mb-2">Piper Legal / Jeremy Piper (P63008)</h4>
                      <p className="text-sm text-muted-foreground mb-1">601 S. Saginaw St., Suite 202</p>
                      <p className="text-sm text-muted-foreground mb-1">Flint, MI 48502</p>
                      <p className="text-sm text-muted-foreground">Phone: (810) 235-2558</p>
                    </div>
                    <div className="bg-muted/30 p-4 rounded-lg">
                      <h5 className="font-medium text-foreground mb-2 flex items-center gap-2">
                        <AlertCircle className="w-4 h-4 text-destructive" />
                        Potential Conflict
                      </h5>
                      <p className="text-sm text-muted-foreground">
                        HOA MI Retail Homes LLC shares address with Piper Legal, suggesting potential attorney-client 
                        and physical location overlap with legal significance.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Government Agencies */}
              <Card className="lg:col-span-2">
                <CardHeader>
                  <CardTitle>Government Agencies Involved</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                    <div className="p-3 rounded-lg bg-secondary/50">
                      <h5 className="font-medium text-foreground mb-1">EGLE</h5>
                      <p className="text-xs text-muted-foreground">Environmental violations</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50">
                      <h5 className="font-medium text-foreground mb-1">MDHHS</h5>
                      <p className="text-xs text-muted-foreground">Housing assistance</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50">
                      <h5 className="font-medium text-foreground mb-1">LARA</h5>
                      <p className="text-xs text-muted-foreground">Licensing & regulatory</p>
                    </div>
                    <div className="p-3 rounded-lg bg-secondary/50">
                      <h5 className="font-medium text-foreground mb-1">Muskegon County</h5>
                      <p className="text-xs text-muted-foreground">Health Department</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>

      {/* Footer */}
      <footer className="border-t border-border mt-16 py-8 bg-card/30">
        <div className="container">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            <p className="text-sm text-muted-foreground">
              Document Blueprint Prepared By: <span className="font-medium text-foreground">Manus AI Analysis System</span>
            </p>
            <div className="flex gap-4 text-sm text-muted-foreground">
              <span>Classification: Legal Case Documentation</span>
              <Separator orientation="vertical" className="h-4" />
              <span>Confidentiality: Attorney Work Product</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
