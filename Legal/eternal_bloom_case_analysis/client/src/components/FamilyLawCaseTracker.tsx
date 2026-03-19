import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { familyLawCases, parentingTimeViolations, litigationOSFramework } from '@/data/family_law_cases';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { AlertTriangle, Calendar, FileText, Users, Scale, Clock, CheckCircle2, XCircle } from 'lucide-react';

export function FamilyLawCaseTracker() {
  const [selectedCase, setSelectedCase] = useState(familyLawCases[0]);

  // Calculate statistics
  const totalCases = familyLawCases.length;
  const activeCases = familyLawCases.filter(c => c.status === 'Active' || c.status === 'Post-Judgment').length;
  const totalViolations = parentingTimeViolations.length;
  const criticalViolations = parentingTimeViolations.filter(v => v.severity === 'Critical').length;

  // Violation severity distribution
  const violationSeverity = [
    { name: 'Critical', value: parentingTimeViolations.filter(v => v.severity === 'Critical').length, fill: '#dc2626' },
    { name: 'High', value: parentingTimeViolations.filter(v => v.severity === 'High').length, fill: '#ea580c' },
    { name: 'Medium', value: parentingTimeViolations.filter(v => v.severity === 'Medium').length, fill: '#f59e0b' },
    { name: 'Low', value: parentingTimeViolations.filter(v => v.severity === 'Low').length, fill: '#10b981' }
  ];

  // Case type distribution
  const caseTypeDistribution = [
    { name: 'DC (Custody)', value: familyLawCases.filter(c => c.caseType === 'DC').length, fill: '#3b82f6' },
    { name: 'PP (PPO)', value: familyLawCases.filter(c => c.caseType === 'PP').length, fill: '#8b5cf6' },
    { name: 'DS (Support)', value: familyLawCases.filter(c => c.caseType === 'DS').length, fill: '#06b6d4' }
  ];

  // Violations by type
  const violationsByType = [
    { name: 'Suspension', count: parentingTimeViolations.filter(v => v.type === 'Suspension').length },
    { name: 'Denial', count: parentingTimeViolations.filter(v => v.type === 'Denial').length },
    { name: 'Delay', count: parentingTimeViolations.filter(v => v.type === 'Delay').length },
    { name: 'Modification', count: parentingTimeViolations.filter(v => v.type === 'Modification').length },
    { name: 'Contempt', count: parentingTimeViolations.filter(v => v.type === 'Contempt').length }
  ];

  return (
    <div className="space-y-6">
      {/* Statistics Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalCases}</div>
            <p className="text-xs text-muted-foreground mt-1">{activeCases} active/post-judgment</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Parenting Time Violations</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{totalViolations}</div>
            <p className="text-xs text-destructive mt-1">{criticalViolations} critical</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">Primary Judge</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-semibold">Jenny L. McNeill</div>
            <p className="text-xs text-muted-foreground mt-1">14th Circuit, Muskegon</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium text-muted-foreground">LitigationOS Framework</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm font-semibold">Active</div>
            <p className="text-xs text-muted-foreground mt-1">3 operational modes</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Tabs */}
      <Tabs defaultValue="cases" className="space-y-6">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="cases">Cases</TabsTrigger>
          <TabsTrigger value="violations">Violations</TabsTrigger>
          <TabsTrigger value="timeline">Timeline</TabsTrigger>
          <TabsTrigger value="framework">LitigationOS</TabsTrigger>
          <TabsTrigger value="analysis">Analysis</TabsTrigger>
        </TabsList>

        {/* Cases Tab */}
        <TabsContent value="cases" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
            {/* Case Selection */}
            <div className="space-y-4">
              <h3 className="font-semibold text-lg">Family Law Cases</h3>
              {familyLawCases.map(caseItem => (
                <Card
                  key={caseItem.id}
                  className={`cursor-pointer transition-all ${selectedCase.id === caseItem.id ? 'ring-2 ring-primary' : ''}`}
                  onClick={() => setSelectedCase(caseItem)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <CardTitle className="text-sm">{caseItem.caseNumber}</CardTitle>
                        <CardDescription className="text-xs mt-1">{caseItem.title}</CardDescription>
                      </div>
                      <Badge variant={caseItem.status === 'Active' ? 'default' : 'secondary'}>
                        {caseItem.status}
                      </Badge>
                    </div>
                  </CardHeader>
                </Card>
              ))}
            </div>

            {/* Case Details */}
            <div className="lg:col-span-2 space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>{selectedCase.title}</CardTitle>
                  <CardDescription>{selectedCase.caseNumber}</CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Plaintiff</p>
                      <p className="font-semibold">{selectedCase.plaintiff}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Defendant</p>
                      <p className="font-semibold">{selectedCase.defendant}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Court</p>
                      <p className="font-semibold text-sm">{selectedCase.court}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Judge</p>
                      <p className="font-semibold text-sm">{selectedCase.judge}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">County</p>
                      <p className="font-semibold">{selectedCase.county}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Filed</p>
                      <p className="font-semibold">{selectedCase.filingDate}</p>
                    </div>
                  </div>

                  <div>
                    <p className="text-sm font-semibold mb-2">Summary</p>
                    <p className="text-sm text-muted-foreground">{selectedCase.summary}</p>
                  </div>

                  <div>
                    <p className="text-sm font-semibold mb-2">Legal Issues</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedCase.issues.slice(0, 5).map((issue, idx) => (
                        <Badge key={idx} variant="outline" className="text-xs">
                          {issue}
                        </Badge>
                      ))}
                      {selectedCase.issues.length > 5 && (
                        <Badge variant="outline" className="text-xs">
                          +{selectedCase.issues.length - 5} more
                        </Badge>
                      )}
                    </div>
                  </div>

                  {selectedCase.violations && selectedCase.violations.length > 0 && (
                    <div>
                      <p className="text-sm font-semibold mb-2 flex items-center gap-2">
                        <AlertTriangle className="w-4 h-4 text-destructive" />
                        Documented Violations
                      </p>
                      <ul className="text-sm space-y-1">
                        {selectedCase.violations.slice(0, 3).map((v, idx) => (
                          <li key={idx} className="text-muted-foreground">• {v}</li>
                        ))}
                        {selectedCase.violations.length > 3 && (
                          <li className="text-muted-foreground">• +{selectedCase.violations.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </TabsContent>

        {/* Violations Tab */}
        <TabsContent value="violations" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Severity Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Violations by Severity</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={violationSeverity}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {violationSeverity.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Violations by Type */}
            <Card>
              <CardHeader>
                <CardTitle>Violations by Type</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <BarChart data={violationsByType}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" angle={-45} textAnchor="end" height={80} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#3b82f6" />
                  </BarChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>
          </div>

          {/* Violations List */}
          <Card>
            <CardHeader>
              <CardTitle>Detailed Violations</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {parentingTimeViolations.map(violation => (
                  <div key={violation.id} className="border rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <p className="font-semibold text-sm">{violation.description}</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          <Calendar className="w-3 h-3 inline mr-1" />
                          {violation.date} | Type: {violation.type}
                        </p>
                      </div>
                      <Badge variant={violation.severity === 'Critical' ? 'destructive' : 'secondary'}>
                        {violation.severity}
                      </Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      <p className="font-semibold mt-2">Remedy: {violation.remedy}</p>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Timeline Tab */}
        <TabsContent value="timeline" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Case Timeline</CardTitle>
              <CardDescription>Key dates and milestones across all family law cases</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {familyLawCases.map(caseItem => (
                  <div key={caseItem.id}>
                    <h4 className="font-semibold text-sm mb-3">{caseItem.caseNumber}</h4>
                    <div className="space-y-2 ml-4 border-l-2 border-primary pl-4">
                      {caseItem.keyDates.map((date, idx) => (
                        <div key={idx} className="flex gap-3">
                          <div className="w-2 h-2 rounded-full bg-primary mt-1.5 flex-shrink-0" />
                          <div>
                            <p className="text-sm font-semibold">{date.event}</p>
                            <p className="text-xs text-muted-foreground">{date.date}</p>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* LitigationOS Framework Tab */}
        <TabsContent value="framework" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>{litigationOSFramework.name}</CardTitle>
              <CardDescription>Build: {litigationOSFramework.buildDate}</CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              {/* Operational Modes */}
              <div>
                <h4 className="font-semibold mb-3">Operational Modes</h4>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {/* Harvest Mode */}
                  <div className="border rounded-lg p-4">
                    <h5 className="font-semibold text-sm mb-2">HARVEST MODE</h5>
                    <p className="text-xs text-muted-foreground mb-3">{litigationOSFramework.modes.harvest.goal}</p>
                    <div className="space-y-1">
                      {litigationOSFramework.modes.harvest.outputs.slice(0, 4).map((output, idx) => (
                        <p key={idx} className="text-xs flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-green-600" />
                          {output}
                        </p>
                      ))}
                    </div>
                  </div>

                  {/* Analysis Mode */}
                  <div className="border rounded-lg p-4">
                    <h5 className="font-semibold text-sm mb-2">ANALYSIS MODE</h5>
                    <p className="text-xs text-muted-foreground mb-3">{litigationOSFramework.modes.analysis.goal}</p>
                    <div className="space-y-1">
                      {litigationOSFramework.modes.analysis.outputs.map((output, idx) => (
                        <p key={idx} className="text-xs flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-blue-600" />
                          {output}
                        </p>
                      ))}
                    </div>
                  </div>

                  {/* Filing Mode */}
                  <div className="border rounded-lg p-4">
                    <h5 className="font-semibold text-sm mb-2">FILING MODE</h5>
                    <p className="text-xs text-muted-foreground mb-3">{litigationOSFramework.modes.filing.goal}</p>
                    <div className="space-y-1">
                      {litigationOSFramework.modes.filing.outputs.map((output, idx) => (
                        <p key={idx} className="text-xs flex items-center gap-2">
                          <CheckCircle2 className="w-3 h-3 text-purple-600" />
                          {output}
                        </p>
                      ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Absolute Governors */}
              <div>
                <h4 className="font-semibold mb-3">Absolute Governors (Fail-Closed)</h4>
                <div className="space-y-2">
                  {litigationOSFramework.governors.map((gov, idx) => (
                    <div key={idx} className="flex gap-3 text-sm">
                      <XCircle className="w-4 h-4 text-destructive flex-shrink-0 mt-0.5" />
                      <p className="text-muted-foreground">{gov}</p>
                    </div>
                  ))}
                </div>
              </div>

              {/* Data Structures */}
              <div>
                <h4 className="font-semibold mb-3">Key Data Structures</h4>
                <div className="space-y-2">
                  {litigationOSFramework.dataStructures.map((ds, idx) => (
                    <div key={idx} className="flex justify-between items-center text-sm border-b pb-2">
                      <span className="font-medium">{ds.name}</span>
                      <span className="text-muted-foreground">{ds.size}</span>
                    </div>
                  ))}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Analysis Tab */}
        <TabsContent value="analysis" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Case Type Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>Case Type Distribution</CardTitle>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={caseTypeDistribution}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, value }) => `${name}: ${value}`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {caseTypeDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Case Status */}
            <Card>
              <CardHeader>
                <CardTitle>Case Status Overview</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {['Active', 'Post-Judgment', 'Closed', 'Appeal'].map(status => {
                    const count = familyLawCases.filter(c => c.status === status).length;
                    return (
                      <div key={status} className="flex justify-between items-center">
                        <span className="text-sm">{status}</span>
                        <Badge variant="outline">{count}</Badge>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Key Findings */}
          <Card>
            <CardHeader>
              <CardTitle>Key Findings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex gap-3">
                <AlertTriangle className="w-5 h-5 text-destructive flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Critical Violations Identified</p>
                  <p className="text-sm text-muted-foreground">{criticalViolations} critical-level parenting time violations documented with evidence</p>
                </div>
              </div>
              <div className="flex gap-3">
                <Scale className="w-5 h-5 text-primary flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Judicial Misconduct Allegations</p>
                  <p className="text-sm text-muted-foreground">Multiple violations linked to Judge Jenny L. McNeill's orders and decisions</p>
                </div>
              </div>
              <div className="flex gap-3">
                <FileText className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" />
                <div>
                  <p className="font-semibold text-sm">Court of Appeals Brief Prepared</p>
                  <p className="text-sm text-muted-foreground">Draft appellant's brief on appeal filed with request for disqualification</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
