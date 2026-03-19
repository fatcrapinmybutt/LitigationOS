import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertCircle, ArrowRight, Shield } from 'lucide-react';

interface LegalTheory {
  id: string;
  name: string;
  category: string;
  severity: 'critical' | 'high' | 'medium' | 'low';
  authorities: string[];
  elements: string[];
  supportingFacts: string[];
  remedies: string[];
}

const legalTheories: LegalTheory[] = [
  {
    id: 'habitability',
    name: 'Warranty of Habitability (MCL 554.139)',
    category: 'Housing Law',
    severity: 'critical',
    authorities: ['MCL 554.139', 'Michigan Compiled Laws', 'Common Law'],
    elements: [
      'Landlord-tenant relationship',
      'Premises unfit for intended use',
      'Landlord knowledge or notice',
      'Failure to repair within reasonable time',
    ],
    supportingFacts: [
      'Sewage leak on property grounds',
      'EGLE environmental violation',
      'Health department citation',
      'Photographic evidence of conditions',
    ],
    remedies: ['Rent abatement', 'Damages', 'Lease termination', 'Injunctive relief'],
  },
  {
    id: 'retaliatory-eviction',
    name: 'Retaliatory Eviction (MCL 600.2919a)',
    category: 'Tenant Protection',
    severity: 'high',
    authorities: ['MCL 600.2919a', 'Michigan Compiled Laws', 'Public Policy'],
    elements: [
      'Protected activity by tenant',
      'Landlord knowledge of activity',
      'Adverse action within 90 days',
      'Causal connection',
    ],
    supportingFacts: [
      'Tenant reported EGLE violations',
      'Tenant sought housing assistance',
      'Eviction filed shortly after complaints',
      'Pattern of retaliation documented',
    ],
    remedies: ['Dismissal of eviction', 'Damages', 'Attorney fees', 'Injunctive relief'],
  },
  {
    id: 'environmental-violation',
    name: 'Environmental Violations (EGLE Part 31)',
    category: 'Environmental Law',
    severity: 'critical',
    authorities: ['EGLE Regulations', 'MCL 324.3101 et seq.', 'Federal CWA'],
    elements: [
      'Discharge of pollutants',
      'Violation of environmental standards',
      'Impact on human health',
      'Failure to remediate',
    ],
    supportingFacts: [
      'Raw sewage discharge documented',
      'EGLE violation notice issued',
      'Health hazard to residents',
      'Property unfit for habitation',
    ],
    remedies: ['Abatement order', 'Remediation', 'Damages', 'Penalties'],
  },
  {
    id: 'due-process',
    name: 'Due Process Violation (14th Amendment)',
    category: 'Constitutional Law',
    severity: 'high',
    authorities: ['U.S. Constitution 14th Amendment', '42 U.S.C. § 1983', 'MCR 2.105/2.107'],
    elements: [
      'State action',
      'Deprivation of protected interest',
      'Lack of procedural due process',
      'Causation',
    ],
    supportingFacts: [
      'Improper service of PPO documents',
      'Unauthorized third-party service',
      'Violation of MCR service rules',
      'Emotional distress to minor child',
    ],
    remedies: ['Damages', 'Injunctive relief', 'Dismissal of proceedings', 'Attorney fees'],
  },
  {
    id: 'breach-contract',
    name: 'Breach of Lease Agreement',
    category: 'Contract Law',
    severity: 'medium',
    authorities: ['MCL 440.2201 et seq.', 'Common Law', 'Lease Terms'],
    elements: [
      'Valid lease agreement',
      'Landlord breach of duties',
      'Tenant reliance',
      'Damages',
    ],
    supportingFacts: [
      'Lease requires habitable premises',
      'Landlord failed to maintain conditions',
      'Unauthorized billing charges',
      'MDHHS payment offset disputes',
    ],
    remedies: ['Damages', 'Specific performance', 'Lease termination', 'Restitution'],
  },
  {
    id: 'mobile-home-act',
    name: 'Mobile Home Commission Act Violations (MCL 125.2301)',
    category: 'Mobile Home Law',
    severity: 'medium',
    authorities: ['MCL 125.2301 et seq.', 'Mobile Home Commission', 'Regulatory Rules'],
    elements: [
      'Mobile home park operation',
      'Violation of statutory duties',
      'Unreasonable rules or practices',
      'Harm to residents',
    ],
    supportingFacts: [
      'Shady Oaks operates as MHP',
      'Excessive or unauthorized charges',
      'Violation of resident rights',
      'Inadequate maintenance standards',
    ],
    remedies: ['Damages', 'Injunctive relief', 'Rule invalidation', 'Attorney fees'],
  },
];

const getSeverityColor = (severity: string) => {
  switch (severity) {
    case 'critical':
      return 'bg-destructive text-destructive-foreground';
    case 'high':
      return 'bg-accent text-accent-foreground';
    case 'medium':
      return 'bg-secondary text-secondary-foreground';
    case 'low':
      return 'bg-muted text-muted-foreground';
    default:
      return 'bg-secondary text-secondary-foreground';
  }
};

export function LegalDependencyMap() {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-6 h-6 text-accent" />
            Legal Dependency Map
          </CardTitle>
          <CardDescription>
            How different legal theories support the case and their supporting facts
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {legalTheories.map((theory, index) => (
              <div key={theory.id} className="border border-border rounded-lg p-5 hover:shadow-md transition-shadow">
                {/* Header */}
                <div className="flex items-start justify-between gap-4 mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-foreground">{theory.name}</h3>
                    <p className="text-sm text-muted-foreground mt-1">{theory.category}</p>
                  </div>
                  <Badge className={getSeverityColor(theory.severity)}>
                    {theory.severity.toUpperCase()}
                  </Badge>
                </div>

                {/* Authorities */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                    <Shield className="w-4 h-4 text-accent" />
                    Legal Authorities
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {theory.authorities.map((auth) => (
                      <Badge key={auth} variant="outline" className="text-xs">
                        {auth}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Elements */}
                <div className="mb-4">
                  <h4 className="text-sm font-semibold text-foreground mb-2">Required Elements</h4>
                  <ul className="space-y-2">
                    {theory.elements.map((element, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <span className="text-accent mt-1">•</span>
                        <span>{element}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Supporting Facts */}
                <div className="mb-4 p-3 bg-secondary/30 rounded-lg">
                  <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                    <AlertCircle className="w-4 h-4 text-accent" />
                    Supporting Facts from Case
                  </h4>
                  <ul className="space-y-2">
                    {theory.supportingFacts.map((fact, idx) => (
                      <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                        <ArrowRight className="w-3 h-3 text-accent mt-1 flex-shrink-0" />
                        <span>{fact}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                {/* Remedies */}
                <div>
                  <h4 className="text-sm font-semibold text-foreground mb-2">Available Remedies</h4>
                  <div className="flex flex-wrap gap-2">
                    {theory.remedies.map((remedy) => (
                      <Badge key={remedy} variant="secondary" className="text-xs bg-chart-1 text-accent-foreground">
                        {remedy}
                      </Badge>
                    ))}
                  </div>
                </div>

                {/* Divider */}
                {index < legalTheories.length - 1 && <div className="mt-5 border-t border-border" />}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Summary Card */}
      <Card className="bg-accent/5 border-accent/20">
        <CardHeader>
          <CardTitle className="text-lg">Case Strength Analysis</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-3 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-xs text-muted-foreground mb-1">Critical Issues</p>
              <p className="text-2xl font-bold text-destructive">2</p>
              <p className="text-xs text-muted-foreground mt-1">Habitability & Environmental</p>
            </div>
            <div className="p-3 rounded-lg bg-accent/10 border border-accent/20">
              <p className="text-xs text-muted-foreground mb-1">High Priority Issues</p>
              <p className="text-2xl font-bold text-accent">2</p>
              <p className="text-xs text-muted-foreground mt-1">Retaliation & Due Process</p>
            </div>
            <div className="p-3 rounded-lg bg-chart-2/10 border border-chart-2/20">
              <p className="text-xs text-muted-foreground mb-1">Supporting Theories</p>
              <p className="text-2xl font-bold text-chart-2">2</p>
              <p className="text-xs text-muted-foreground mt-1">Contract & MH Act</p>
            </div>
            <div className="p-3 rounded-lg bg-primary/10 border border-primary/20">
              <p className="text-xs text-muted-foreground mb-1">Total Legal Theories</p>
              <p className="text-2xl font-bold text-primary">6</p>
              <p className="text-xs text-muted-foreground mt-1">Multi-pronged approach</p>
            </div>
          </div>

          <div className="p-4 bg-background rounded-lg border border-border">
            <p className="text-sm text-foreground">
              <strong>Strategic Insight:</strong> The case has multiple strong legal theories with substantial supporting 
              evidence. The critical issues (habitability and environmental violations) provide the strongest foundation, 
              while the retaliation and due process claims add significant leverage. The contract and Mobile Home Act 
              violations provide additional remedies and demonstrate a pattern of misconduct.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
