import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Search, BookOpen, AlertCircle, Lightbulb } from 'lucide-react';

interface KnowledgeItem {
  id: string;
  name: string;
  label: string;
  kind: string;
}

interface KnowledgeBaseData {
  authorities: KnowledgeItem[];
  cases: KnowledgeItem[];
  concepts: KnowledgeItem[];
}

export function LegalKnowledgeBase() {
  const [data, setData] = useState<KnowledgeBaseData | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedItem, setSelectedItem] = useState<KnowledgeItem | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/legal_graph_data.json')
      .then(res => res.json())
      .then(graphData => {
        setData({
          authorities: graphData.authorities || [],
          cases: graphData.cases || [],
          concepts: graphData.concepts || [],
        });
        setLoading(false);
      })
      .catch(err => {
        console.error('Failed to load knowledge base:', err);
        setLoading(false);
      });
  }, []);

  const filterItems = (items: KnowledgeItem[]) => {
    if (!searchTerm) return items;
    return items.filter(item =>
      item.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      item.label.toLowerCase().includes(searchTerm.toLowerCase())
    );
  };

  const getItemBadgeColor = (kind: string) => {
    switch (kind) {
      case 'authority':
        return 'bg-chart-1 text-accent-foreground';
      case 'violation':
        return 'bg-destructive text-destructive-foreground';
      case 'concept':
        return 'bg-chart-2 text-foreground';
      default:
        return 'bg-secondary text-secondary-foreground';
    }
  };

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Legal Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-96">
            <p className="text-muted-foreground">Loading knowledge base...</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!data) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Legal Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-96">
            <p className="text-destructive">Failed to load knowledge base</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="w-6 h-6 text-accent" />
          Legal Knowledge Base
        </CardTitle>
        <CardDescription>
          Searchable database of legal authorities, case law, and legal concepts
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-3 w-4 h-4 text-muted-foreground" />
          <Input
            placeholder="Search by name, statute, or concept..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10"
          />
        </div>

        {/* Tabs */}
        <Tabs defaultValue="authorities" className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="authorities">
              Authorities ({data.authorities.length})
            </TabsTrigger>
            <TabsTrigger value="cases">
              Cases ({data.cases.length})
            </TabsTrigger>
            <TabsTrigger value="concepts">
              Concepts ({data.concepts.length})
            </TabsTrigger>
          </TabsList>

          {/* Authorities Tab */}
          <TabsContent value="authorities">
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-2">
                {filterItems(data.authorities).length > 0 ? (
                  filterItems(data.authorities).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => setSelectedItem(item)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedItem?.id === item.id
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-accent/50 hover:bg-secondary/30'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-foreground text-sm">{item.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
                        </div>
                        <Badge variant="secondary" className={getItemBadgeColor(item.kind)}>
                          {item.kind}
                        </Badge>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                    <Search className="w-8 h-8 mb-2 opacity-50" />
                    <p className="text-sm">No authorities found</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Cases Tab */}
          <TabsContent value="cases">
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-2">
                {filterItems(data.cases).length > 0 ? (
                  filterItems(data.cases).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => setSelectedItem(item)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedItem?.id === item.id
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-accent/50 hover:bg-secondary/30'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-foreground text-sm">{item.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
                        </div>
                        <Badge variant="secondary" className="bg-destructive text-destructive-foreground">
                          Case
                        </Badge>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                    <AlertCircle className="w-8 h-8 mb-2 opacity-50" />
                    <p className="text-sm">No cases found</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>

          {/* Concepts Tab */}
          <TabsContent value="concepts">
            <ScrollArea className="h-[400px] pr-4">
              <div className="space-y-2">
                {filterItems(data.concepts).length > 0 ? (
                  filterItems(data.concepts).map((item) => (
                    <div
                      key={item.id}
                      onClick={() => setSelectedItem(item)}
                      className={`p-3 rounded-lg border cursor-pointer transition-all ${
                        selectedItem?.id === item.id
                          ? 'border-accent bg-accent/10'
                          : 'border-border hover:border-accent/50 hover:bg-secondary/30'
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-foreground text-sm">{item.name}</h4>
                          <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
                        </div>
                        <Badge variant="secondary" className={getItemBadgeColor(item.kind)}>
                          {item.kind}
                        </Badge>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
                    <Lightbulb className="w-8 h-8 mb-2 opacity-50" />
                    <p className="text-sm">No concepts found</p>
                  </div>
                )}
              </div>
            </ScrollArea>
          </TabsContent>
        </Tabs>

        {/* Selected Item Details */}
        {selectedItem && (
          <div className="p-4 bg-muted/30 rounded-lg border border-border space-y-3">
            <div>
              <h3 className="font-semibold text-foreground text-lg">{selectedItem.name}</h3>
              <p className="text-sm text-muted-foreground mt-1">{selectedItem.label}</p>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Badge className={getItemBadgeColor(selectedItem.kind)}>
                {selectedItem.kind.toUpperCase()}
              </Badge>
              <Badge variant="outline">ID: {selectedItem.id.substring(0, 12)}...</Badge>
            </div>
            <p className="text-xs text-muted-foreground">
              Click on other items to compare or explore relationships
            </p>
          </div>
        )}

        {/* Statistics */}
        <div className="grid grid-cols-3 gap-4 p-4 bg-secondary/30 rounded-lg">
          <div>
            <p className="text-xs text-muted-foreground">Total Authorities</p>
            <p className="text-2xl font-bold text-foreground">{data.authorities.length}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total Cases</p>
            <p className="text-2xl font-bold text-foreground">{data.cases.length}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Total Concepts</p>
            <p className="text-2xl font-bold text-foreground">{data.concepts.length}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
