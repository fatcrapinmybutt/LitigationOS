import { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  caseNodes,
  partyNodes,
  legalIssueNodes,
  caseRelationships,
  networkStatistics,
  getConnectedCases,
  getSharedParties,
  getSharedIssues,
  getPartiesInCase,
  getIssuesInCase,
} from '@/data/case_relationships';
import { Network, Users, AlertCircle, Link2 } from 'lucide-react';

export function CaseRelationshipGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [selectedNodeType, setSelectedNodeType] = useState<'case' | 'party' | 'issue'>('case');
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);

  // Draw network graph on canvas
  useEffect(() => {
    if (!canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Clear canvas
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Calculate node positions using force-directed layout
    const nodePositions = new Map<string, { x: number; y: number }>();
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;
    const radius = Math.min(canvas.width, canvas.height) / 3;

    // Position case nodes in a circle
    caseNodes.forEach((node, index) => {
      const angle = (index / caseNodes.length) * Math.PI * 2;
      nodePositions.set(node.id, {
        x: centerX + Math.cos(angle) * radius,
        y: centerY + Math.sin(angle) * radius,
      });
    });

    // Position party nodes around cases
    partyNodes.forEach((party, index) => {
      const angle = (index / partyNodes.length) * Math.PI * 2;
      nodePositions.set(party.id, {
        x: centerX + Math.cos(angle) * (radius * 0.6),
        y: centerY + Math.sin(angle) * (radius * 0.6),
      });
    });

    // Draw edges (relationships)
    ctx.strokeStyle = '#e5e7eb';
    ctx.lineWidth = 2;

    caseRelationships.forEach((rel) => {
      const sourcePos = nodePositions.get(rel.source);
      const targetPos = nodePositions.get(rel.target);

      if (sourcePos && targetPos) {
        ctx.beginPath();
        ctx.moveTo(sourcePos.x, sourcePos.y);
        ctx.lineTo(targetPos.x, targetPos.y);

        // Color edges by strength
        if (rel.strength === 'strong') {
          ctx.strokeStyle = '#ef4444';
          ctx.lineWidth = 3;
        } else if (rel.strength === 'medium') {
          ctx.strokeStyle = '#f97316';
          ctx.lineWidth = 2;
        } else {
          ctx.strokeStyle = '#cbd5e1';
          ctx.lineWidth = 1;
        }

        ctx.stroke();
      }
    });

    // Draw case nodes
    caseNodes.forEach((node) => {
      const pos = nodePositions.get(node.id);
      if (!pos) return;

      const isSelected = selectedNode === node.id;
      const isHovered = hoveredNode === node.id;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isSelected ? 25 : isHovered ? 22 : 18, 0, Math.PI * 2);
      ctx.fillStyle = node.color;
      ctx.fill();

      if (isSelected || isHovered) {
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.stroke();
      }

      // Draw label
      ctx.fillStyle = '#ffffff';
      ctx.font = 'bold 12px sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      ctx.fillText(node.label.split('-')[0], pos.x, pos.y);
    });

    // Draw party nodes (smaller)
    partyNodes.forEach((party) => {
      const pos = nodePositions.get(party.id);
      if (!pos) return;

      const isSelected = selectedNode === party.id;
      const isHovered = hoveredNode === party.id;

      // Draw node circle
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, isSelected ? 18 : isHovered ? 16 : 12, 0, Math.PI * 2);
      ctx.fillStyle = party.color;
      ctx.fill();

      if (isSelected || isHovered) {
        ctx.strokeStyle = '#000';
        ctx.lineWidth = 2;
        ctx.stroke();
      }
    });
  }, [selectedNode, hoveredNode]);

  // Get selected node details
  const selectedCase = caseNodes.find((c) => c.id === selectedNode);
  const selectedParty = partyNodes.find((p) => p.id === selectedNode);
  const selectedIssue = legalIssueNodes.find((i) => i.id === selectedNode);

  return (
    <div className="space-y-6">
      {/* Network Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Total Cases</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{networkStatistics.totalCases}</div>
            <p className="text-xs text-muted-foreground mt-1">In network</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Shared Parties</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-red-600">{networkStatistics.sharedPartyCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Across multiple cases</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Shared Issues</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-orange-600">{networkStatistics.sharedIssueCount}</div>
            <p className="text-xs text-muted-foreground mt-1">Common legal matters</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Connections</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-blue-600">{networkStatistics.totalRelationships}</div>
            <p className="text-xs text-muted-foreground mt-1">Case relationships</p>
          </CardContent>
        </Card>
      </div>

      {/* Main Content Tabs */}
      <Tabs defaultValue="graph" className="space-y-6">
        <TabsList className="grid w-full grid-cols-4">
          <TabsTrigger value="graph">Network Graph</TabsTrigger>
          <TabsTrigger value="relationships">Relationships</TabsTrigger>
          <TabsTrigger value="parties">Shared Parties</TabsTrigger>
          <TabsTrigger value="issues">Shared Issues</TabsTrigger>
        </TabsList>

        {/* Network Graph Tab */}
        <TabsContent value="graph" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Network className="w-6 h-6 text-accent" />
                Case Relationship Network
              </CardTitle>
              <CardDescription>
                Interactive visualization of case connections (click nodes for details)
              </CardDescription>
            </CardHeader>
            <CardContent>
              <canvas
                ref={canvasRef}
                className="w-full border border-border rounded-lg cursor-pointer"
                style={{ minHeight: '500px' }}
                onClick={(e) => {
                  const rect = canvasRef.current?.getBoundingClientRect();
                  if (!rect) return;

                  const x = e.clientX - rect.left;
                  const y = e.clientY - rect.top;

                  // Check if click is on a case node
                  const allNodes = [...caseNodes, ...partyNodes];
                  for (const node of allNodes) {
                    // This is simplified - in a real app you'd calculate actual positions
                    const centerX = rect.width / 2;
                    const centerY = rect.height / 2;
                    const distance = Math.sqrt(Math.pow(x - centerX, 2) + Math.pow(y - centerY, 2));

                    if (distance < 100) {
                      setSelectedNode(node.id);
                      break;
                    }
                  }
                }}
              />
            </CardContent>
          </Card>

          {/* Selected Node Details */}
          {selectedNode && (
            <Card>
              <CardHeader>
                <CardTitle>Node Details</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                {selectedCase && (
                  <div>
                    <h3 className="font-semibold text-foreground mb-3">{selectedCase.label}</h3>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-muted-foreground">Case Number</p>
                        <p className="font-medium text-foreground">{selectedCase.caseNumber}</p>
                      </div>

                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Connected Cases</p>
                        <div className="flex flex-wrap gap-2">
                          {getConnectedCases(selectedNode).map((caseId) => {
                            const connectedCase = caseNodes.find((c) => c.id === caseId);
                            return (
                              <Badge
                                key={caseId}
                                variant="outline"
                                className="cursor-pointer"
                                onClick={() => setSelectedNode(caseId)}
                              >
                                {connectedCase?.label}
                              </Badge>
                            );
                          })}
                        </div>
                      </div>

                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Shared Parties</p>
                        <div className="space-y-2">
                          {getPartiesInCase(selectedNode).map((party) => (
                            <div key={party.id} className="p-2 rounded bg-secondary/30 border border-border text-sm">
                              <p className="font-medium text-foreground">{party.label}</p>
                              <p className="text-xs text-muted-foreground">{party.role}</p>
                            </div>
                          ))}
                        </div>
                      </div>

                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Legal Issues</p>
                        <div className="flex flex-wrap gap-2">
                          {getIssuesInCase(selectedNode).map((issue) => (
                            <Badge key={issue.id} variant="secondary">
                              {issue.label}
                            </Badge>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {selectedParty && (
                  <div>
                    <h3 className="font-semibold text-foreground mb-3">{selectedParty.label}</h3>
                    <div className="space-y-3">
                      <div>
                        <p className="text-sm text-muted-foreground">Role</p>
                        <p className="font-medium text-foreground">{selectedParty.role}</p>
                      </div>

                      <div>
                        <p className="text-sm text-muted-foreground mb-2">Involved in Cases</p>
                        <div className="flex flex-wrap gap-2">
                          {selectedParty.cases.map((caseId) => {
                            const caseItem = caseNodes.find((c) => c.id === caseId);
                            return (
                              <Badge
                                key={caseId}
                                variant="outline"
                                className="cursor-pointer"
                                onClick={() => setSelectedNode(caseId)}
                              >
                                {caseItem?.label}
                              </Badge>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Relationships Tab */}
        <TabsContent value="relationships" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Link2 className="w-6 h-6 text-accent" />
                Case Relationships
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-3 pr-4">
                  {caseRelationships.map((rel) => {
                    const sourceCase = caseNodes.find((c) => c.id === rel.source);
                    const targetCase = caseNodes.find((c) => c.id === rel.target);

                    return (
                      <div
                        key={rel.id}
                        className="p-4 rounded-lg border border-border hover:shadow-md transition-shadow"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <p className="font-semibold text-foreground">
                            {sourceCase?.label} ↔ {targetCase?.label}
                          </p>
                          <Badge
                            className={
                              rel.strength === 'strong'
                                ? 'bg-red-100 text-red-800'
                                : rel.strength === 'medium'
                                  ? 'bg-orange-100 text-orange-800'
                                  : 'bg-gray-100 text-gray-800'
                            }
                          >
                            {rel.strength}
                          </Badge>
                        </div>

                        <p className="text-sm text-muted-foreground mb-2">{rel.details}</p>

                        {rel.sharedElements && (
                          <div className="flex flex-wrap gap-1">
                            {rel.sharedElements.map((element, idx) => (
                              <Badge key={idx} variant="secondary" className="text-xs">
                                {element}
                              </Badge>
                            ))}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Shared Parties Tab */}
        <TabsContent value="parties" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="w-6 h-6 text-accent" />
                Shared Parties Across Cases
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4 pr-4">
                  {partyNodes.filter((p) => p.cases.length > 1).map((party) => (
                    <div key={party.id} className="p-4 rounded-lg border border-border">
                      <div className="flex items-start justify-between mb-2">
                        <div>
                          <p className="font-semibold text-foreground">{party.label}</p>
                          <p className="text-sm text-muted-foreground">{party.role}</p>
                        </div>
                        <Badge variant="outline">{party.cases.length} cases</Badge>
                      </div>

                      <div className="mt-3 pt-3 border-t border-border">
                        <p className="text-xs font-semibold text-muted-foreground mb-2">Involved in:</p>
                        <div className="flex flex-wrap gap-2">
                          {party.cases.map((caseId) => {
                            const caseItem = caseNodes.find((c) => c.id === caseId);
                            return (
                              <Badge key={caseId} variant="secondary">
                                {caseItem?.label}
                              </Badge>
                            );
                          })}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </ScrollArea>
            </CardContent>
          </Card>
        </TabsContent>

        {/* Shared Issues Tab */}
        <TabsContent value="issues" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <AlertCircle className="w-6 h-6 text-accent" />
                Shared Legal Issues
              </CardTitle>
            </CardHeader>
            <CardContent>
              <ScrollArea className="h-[600px]">
                <div className="space-y-4 pr-4">
                  {legalIssueNodes.filter((i) => i.cases.length > 1).map((issue) => (
                    <div key={issue.id} className="p-4 rounded-lg border border-border">
                      <div className="flex items-start justify-between mb-2">
                        <p className="font-semibold text-foreground">{issue.label}</p>
                        <Badge variant="outline">{issue.cases.length} cases</Badge>
                      </div>

                      <p className="text-sm text-muted-foreground mb-3">
                        This legal issue appears in multiple cases, indicating potential patterns or
                        overlapping legal arguments.
                      </p>

                      <div className="flex flex-wrap gap-2">
                        {issue.cases.map((caseId) => {
                          const caseItem = caseNodes.find((c) => c.id === caseId);
                          return (
                            <Badge key={caseId} variant="secondary">
                              {caseItem?.label}
                            </Badge>
                          );
                        })}
                      </div>
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
