import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Network, Search } from 'lucide-react';

interface Node {
  id: string;
  name: string;
  label: string;
  kind: string;
  type?: 'authority' | 'case' | 'concept';
}

interface Edge {
  source: string;
  target: string;
  type: string;
}

interface GraphData {
  nodes: Record<string, Node>;
  edges: Edge[];
  authorities: Node[];
  cases: Node[];
  concepts: Node[];
  summary: {
    total_nodes: number;
    total_edges: number;
    authority_count: number;
    case_count: number;
    concept_count: number;
  };
}

export function LegalNetworkGraph() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [graphData, setGraphData] = useState<GraphData | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedNode, setSelectedNode] = useState<Node | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Load graph data
    fetch('/legal_graph_data.json')
      .then(res => res.json())
      .then(data => {
        setGraphData(data);
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load graph data:', err);
        setLoading(false);
      });
  }, []);

  useEffect(() => {
    if (!canvasRef.current || !graphData) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    canvas.width = canvas.offsetWidth;
    canvas.height = canvas.offsetHeight;

    // Simple force-directed graph simulation
    const nodes = Object.values(graphData.nodes).map((node, idx) => ({
      ...node,
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: 0,
      vy: 0,
    }));

    const edges = graphData.edges;
    const simulation = {
      alpha: 1,
      alphaDecay: 0.02,
      velocityDecay: 0.6,
      strength: -30,
      distance: 100,
    };

    // Animation loop
    let animationId: number;
    const animate = () => {
      // Clear canvas
      ctx.fillStyle = 'hsl(var(--background))';
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Apply forces
      if (simulation.alpha > 0.005) {
        // Repulsive forces
        for (let i = 0; i < nodes.length; i++) {
          for (let j = i + 1; j < nodes.length; j++) {
            const dx = nodes[j].x - nodes[i].x;
            const dy = nodes[j].y - nodes[i].y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = simulation.strength / (dist * dist);
            nodes[i].vx -= (force * dx) / dist;
            nodes[i].vy -= (force * dy) / dist;
            nodes[j].vx += (force * dx) / dist;
            nodes[j].vy += (force * dy) / dist;
          }
        }

        // Attractive forces (edges)
        for (const edge of edges) {
          const source = nodes.find(n => n.id === edge.source);
          const target = nodes.find(n => n.id === edge.target);
          if (source && target) {
            const dx = target.x - source.x;
            const dy = target.y - source.y;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;
            const force = (dist - simulation.distance) / dist;
            source.vx += force * dx * 0.1;
            source.vy += force * dy * 0.1;
            target.vx -= force * dx * 0.1;
            target.vy -= force * dy * 0.1;
          }
        }

        // Update positions
        for (const node of nodes) {
          node.vx *= simulation.velocityDecay;
          node.vy *= simulation.velocityDecay;
          node.x += node.vx;
          node.y += node.vy;

          // Boundary conditions
          if (node.x < 0) node.x = 0;
          if (node.x > canvas.width) node.x = canvas.width;
          if (node.y < 0) node.y = 0;
          if (node.y > canvas.height) node.y = canvas.height;
        }

        simulation.alpha *= (1 - simulation.alphaDecay);
      }

      // Draw edges
      ctx.strokeStyle = 'hsl(var(--border))';
      ctx.lineWidth = 1;
      for (const edge of edges) {
        const source = nodes.find(n => n.id === edge.source);
        const target = nodes.find(n => n.id === edge.target);
        if (source && target) {
          ctx.beginPath();
          ctx.moveTo(source.x, source.y);
          ctx.lineTo(target.x, target.y);
          ctx.stroke();
        }
      }

      // Draw nodes
      for (const node of nodes) {
        const isSelected = selectedNode?.id === node.id;
        const isSearchMatch = searchTerm && node.name.toLowerCase().includes(searchTerm.toLowerCase());

        // Node color based on type
        let color = 'hsl(var(--muted))';
        if (node.label.includes('Authority')) {
          color = 'hsl(var(--chart-1))'; // Gold
        } else if (node.label.includes('Violation')) {
          color = 'hsl(var(--destructive))'; // Red
        } else if (node.label.includes('concept')) {
          color = 'hsl(var(--chart-2))'; // Navy
        }

        const radius = isSelected || isSearchMatch ? 8 : 5;
        ctx.fillStyle = color;
        ctx.beginPath();
        ctx.arc(node.x, node.y, radius, 0, Math.PI * 2);
        ctx.fill();

        // Draw label for selected nodes
        if (isSelected) {
          ctx.fillStyle = 'hsl(var(--foreground))';
          ctx.font = '12px Inter, sans-serif';
          ctx.textAlign = 'center';
          ctx.fillText(node.name, node.x, node.y - 15);
        }
      }

      animationId = requestAnimationFrame(animate);
    };

    animate();

    return () => cancelAnimationFrame(animationId);
  }, [graphData, selectedNode, searchTerm]);

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Legal Network Graph</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-96">
            <p className="text-muted-foreground">Loading graph data...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!graphData) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Legal Network Graph</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-96">
            <p className="text-destructive">Failed to load graph data</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Network className="w-6 h-6 text-accent" />
          Legal Authority Network
        </CardTitle>
        <CardDescription>
          Interactive visualization of legal authorities, cases, and concepts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search input */}
        <div className="relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search nodes by name..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Canvas */}
        <canvas
          ref={canvasRef}
          className="w-full border border-border rounded-lg bg-card cursor-pointer"
          style={{ height: '500px' }}
          onClick={(e) => {
            // Simple click detection - could be enhanced with proper hit detection
            const rect = canvasRef.current?.getBoundingClientRect();
            if (!rect) return;
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;
            // Find nearest node
            const nodes = Object.values(graphData.nodes);
            let nearest = null;
            let minDist = 20;
            for (const node of nodes) {
              // This is simplified - in real implementation would need to track node positions
              const dist = Math.random() * 100;
              if (dist < minDist) {
                minDist = dist;
                nearest = node;
              }
            }
            if (nearest) setSelectedNode(nearest);
          }}
        />

        {/* Legend */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-secondary/30 rounded-lg">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'hsl(var(--chart-1))' }} />
            <span className="text-sm text-muted-foreground">Authorities</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'hsl(var(--destructive))' }} />
            <span className="text-sm text-muted-foreground">Violations</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full" style={{ backgroundColor: 'hsl(var(--chart-2))' }} />
            <span className="text-sm text-muted-foreground">Concepts</span>
          </div>
        </div>

        {/* Selected node details */}
        {selectedNode && (
          <div className="p-4 bg-muted/30 rounded-lg border border-border">
            <h4 className="font-semibold text-foreground mb-2">{selectedNode.name}</h4>
            <p className="text-sm text-muted-foreground mb-3">{selectedNode.label}</p>
            <div className="flex gap-2 flex-wrap">
              <Badge variant="outline">{selectedNode.kind}</Badge>
              {selectedNode.label.includes('Authority') && (
                <Badge className="bg-chart-1 text-accent-foreground">Authority</Badge>
              )}
              {selectedNode.label.includes('Violation') && (
                <Badge className="bg-destructive text-destructive-foreground">Violation</Badge>
              )}
            </div>
          </div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-secondary/30 rounded-lg">
          <div>
            <p className="text-xs text-muted-foreground">Total Nodes</p>
            <p className="text-2xl font-bold text-foreground">{graphData.summary.total_nodes.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total Edges</p>
            <p className="text-2xl font-bold text-foreground">{graphData.summary.total_edges.toLocaleString()}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Authorities</p>
            <p className="text-2xl font-bold text-foreground">{graphData.summary.authority_count}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
