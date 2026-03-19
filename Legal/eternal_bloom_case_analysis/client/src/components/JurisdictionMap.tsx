import { useEffect, useRef, useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { MapPin, Building2, Scale } from 'lucide-react';
import { multiCaseTracks, caseTypeCategories } from '@/data/multi_case_data';

interface CourtLocation {
  id: string;
  caseId: string;
  caseNumber: string;
  caseType: string;
  courtName: string;
  address: string;
  city: string;
  state: string;
  zipCode: string;
  latitude: number;
  longitude: number;
  color: string;
  judge?: string;
  courtType: string;
}

const courtLocations: CourtLocation[] = [
  {
    id: 'court-dc-1',
    caseId: 'case-2024-1507-dc',
    caseNumber: '2024-1507-DC',
    caseType: 'dc',
    courtName: 'Michigan District Court',
    address: '1200 N. Telegraph Rd',
    city: 'Dearborn',
    state: 'MI',
    zipCode: '48126',
    latitude: 42.3216,
    longitude: -83.1825,
    color: '#8B4513',
    judge: 'Hon. District Judge',
    courtType: 'District Court',
  },
  {
    id: 'court-pp-1',
    caseId: 'case-2023-5907-pp',
    caseNumber: '2023-5907-PP',
    caseType: 'pp',
    courtName: 'Michigan Probate Court',
    address: '500 Griswold St',
    city: 'Detroit',
    state: 'MI',
    zipCode: '48226',
    latitude: 42.3314,
    longitude: -83.0458,
    color: '#4B0082',
    judge: 'Hon. Probate Judge',
    courtType: 'Probate Court',
  },
  {
    id: 'court-lt-1',
    caseId: 'case-2025-25061626-lt',
    caseNumber: '2025-25061626-LT',
    caseType: 'lt',
    courtName: 'Wayne County District Court - Housing Division',
    address: '2 Woodward Ave',
    city: 'Detroit',
    state: 'MI',
    zipCode: '48202',
    latitude: 42.3314,
    longitude: -83.0458,
    color: '#FF6347',
    judge: 'Hon. Housing Judge',
    courtType: 'Housing Division',
  },
  {
    id: 'court-cz-1',
    caseId: 'case-2025-002760-cz',
    caseNumber: '2025-002760-CZ',
    caseType: 'cz',
    courtName: 'Michigan Circuit Court',
    address: '100 Cadillac Square',
    city: 'Detroit',
    state: 'MI',
    zipCode: '48202',
    latitude: 42.3314,
    longitude: -83.0458,
    color: '#20B2AA',
    judge: 'Hon. Circuit Judge',
    courtType: 'Circuit Court',
  },
];

export function JurisdictionMap() {
  const mapRef = useRef<HTMLDivElement>(null);
  const [map, setMap] = useState<google.maps.Map | null>(null);
  const [markers, setMarkers] = useState<google.maps.Marker[]>([]);
  const [selectedCourt, setSelectedCourt] = useState<CourtLocation | null>(null);
  const [filteredCaseType, setFilteredCaseType] = useState<string | null>(null);

  // Initialize map
  useEffect(() => {
    if (!mapRef.current) return;

    const newMap = new google.maps.Map(mapRef.current, {
      zoom: 10,
      center: { lat: 42.3314, lng: -83.0458 }, // Detroit, MI center
      styles: [
        {
          featureType: 'all',
          elementType: 'labels.text.fill',
          stylers: [{ color: '#616161' }],
        },
        {
          featureType: 'water',
          elementType: 'geometry',
          stylers: [{ color: '#e9e9e9' }],
        },
      ],
    });

    setMap(newMap);
  }, []);

  // Add markers to map
  useEffect(() => {
    if (!map) return;

    // Clear existing markers
    markers.forEach((marker) => marker.setMap(null));

    // Filter courts based on selected case type
    const filteredCourts = filteredCaseType
      ? courtLocations.filter((court) => court.caseType === filteredCaseType)
      : courtLocations;

    // Create new markers
    const newMarkers = filteredCourts.map((court) => {
      const marker = new google.maps.Marker({
        position: { lat: court.latitude, lng: court.longitude },
        map: map,
        title: court.courtName,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 12,
          fillColor: court.color,
          fillOpacity: 0.8,
          strokeColor: '#fff',
          strokeWeight: 2,
        },
      });

      // Add click listener
      marker.addListener('click', () => {
        setSelectedCourt(court);
        map.setCenter({ lat: court.latitude, lng: court.longitude });
        map.setZoom(13);
      });

      return marker;
    });

    setMarkers(newMarkers);
  }, [map, filteredCaseType]);

  return (
    <div className="space-y-6">
      {/* Map Container */}
      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-6 h-6 text-accent" />
            Jurisdiction Map - Case Locations
          </CardTitle>
          <CardDescription>
            Geographic distribution of courts for all four legal cases
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            ref={mapRef}
            className="w-full h-[500px] rounded-lg border border-border"
            style={{ minHeight: '500px' }}
          />
        </CardContent>
      </Card>

      {/* Case Type Filter */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Filter by Case Type</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setFilteredCaseType(null)}
              className={`px-4 py-2 rounded-lg border-2 transition-all ${
                filteredCaseType === null
                  ? 'border-accent bg-accent/10'
                  : 'border-border hover:border-accent/50'
              }`}
            >
              All Cases
            </button>
            {Object.entries(caseTypeCategories).map(([key, category]) => (
              <button
                key={key}
                onClick={() => setFilteredCaseType(key)}
                className={`px-4 py-2 rounded-lg border-2 transition-all flex items-center gap-2 ${
                  filteredCaseType === key
                    ? 'border-accent bg-accent/10'
                    : 'border-border hover:border-accent/50'
                }`}
              >
                <span>{category.icon}</span>
                {category.label}
              </button>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Court Details */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Court List */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="w-6 h-6 text-accent" />
              Courts & Jurisdictions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {(filteredCaseType
                ? courtLocations.filter((c) => c.caseType === filteredCaseType)
                : courtLocations
              ).map((court) => (
                <button
                  key={court.id}
                  onClick={() => {
                    setSelectedCourt(court);
                    if (map) {
                      map.setCenter({ lat: court.latitude, lng: court.longitude });
                      map.setZoom(13);
                    }
                  }}
                  className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
                    selectedCourt?.id === court.id
                      ? 'border-accent bg-accent/10'
                      : 'border-border hover:border-accent/50'
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className="w-4 h-4 rounded-full mt-1 flex-shrink-0"
                      style={{ backgroundColor: court.color }}
                    />
                    <div className="flex-1">
                      <p className="font-semibold text-foreground">{court.courtName}</p>
                      <p className="text-sm text-muted-foreground mt-1">{court.caseNumber}</p>
                      <p className="text-xs text-muted-foreground mt-1">
                        {court.address}, {court.city}, {court.state} {court.zipCode}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Selected Court Details */}
        {selectedCourt && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Scale className="w-6 h-6 text-accent" />
                Court Details
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div>
                <p className="text-sm text-muted-foreground">Court Name</p>
                <p className="font-semibold text-foreground">{selectedCourt.courtName}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Case Number</p>
                <p className="font-semibold text-foreground">{selectedCourt.caseNumber}</p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Court Type</p>
                <Badge className="mt-1">{selectedCourt.courtType}</Badge>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Address</p>
                <p className="font-medium text-foreground mt-1">{selectedCourt.address}</p>
                <p className="text-sm text-foreground">
                  {selectedCourt.city}, {selectedCourt.state} {selectedCourt.zipCode}
                </p>
              </div>

              <div>
                <p className="text-sm text-muted-foreground">Presiding Judge</p>
                <p className="font-medium text-foreground">{selectedCourt.judge}</p>
              </div>

              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground">Coordinates</p>
                <p className="text-xs font-mono text-foreground mt-1">
                  {selectedCourt.latitude.toFixed(4)}, {selectedCourt.longitude.toFixed(4)}
                </p>
              </div>

              {/* Related Case */}
              <div className="pt-4 border-t border-border">
                <p className="text-sm text-muted-foreground mb-2">Related Case</p>
                {multiCaseTracks
                  .filter((c) => c.id === selectedCourt.caseId)
                  .map((caseItem) => (
                    <div key={caseItem.id} className="p-3 rounded-lg bg-secondary/30 border border-border">
                      <p className="font-semibold text-foreground">{caseItem.name}</p>
                      <p className="text-xs text-muted-foreground mt-1">{caseItem.description}</p>
                      <div className="flex flex-wrap gap-1 mt-2">
                        {caseItem.legalIssues.slice(0, 2).map((issue, idx) => (
                          <Badge key={idx} variant="secondary" className="text-xs">
                            {issue}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
              </div>
            </CardContent>
          </Card>
        )}
      </div>

      {/* Jurisdiction Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MapPin className="w-6 h-6 text-accent" />
            Jurisdiction Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {courtLocations.map((court) => (
              <div key={court.id} className="flex items-start gap-3 pb-3 border-b border-border last:border-0">
                <div
                  className="w-3 h-3 rounded-full mt-1.5 flex-shrink-0"
                  style={{ backgroundColor: court.color }}
                />
                <div className="flex-1">
                  <div className="flex items-center justify-between mb-1">
                    <p className="font-semibold text-foreground">{court.caseNumber}</p>
                    <Badge variant="outline" className="text-xs">
                      {court.courtType}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground">{court.courtName}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    📍 {court.city}, {court.state}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
