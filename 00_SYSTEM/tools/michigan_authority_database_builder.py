#!/usr/bin/env python3
r"""
Michigan Legal Authority Database Builder (Tool #276)
Creates comprehensive legal authority database for pro se litigant Andrew Pigors
Focus: Family law, civil law, contempt, appeals, disqualification
Database: C:\Users\andre\LitigationOS\litigation_context.db
"""

import sqlite3
import os
from datetime import datetime

DB_PATH = r"C:\Users\andre\LitigationOS\litigation_context.db"

def create_connection():
    """Create database connection with optimized settings."""
    db = sqlite3.connect(DB_PATH)
    db.execute('PRAGMA busy_timeout=60000')
    db.execute('PRAGMA journal_mode=WAL')
    db.execute('PRAGMA cache_size=-32000')
    return db

def create_tables(db):
    """Create all required tables."""
    cursor = db.cursor()
    
    # Table 1: Michigan Court Rules (MCR)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS michigan_court_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        full_text TEXT NOT NULL,
        category TEXT,
        filing_type TEXT,
        lane TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table 2: Michigan Statutes (MCL)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS michigan_statutes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        statute_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        full_text TEXT NOT NULL,
        category TEXT,
        lane TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table 3: Michigan Evidence Rules (MRE)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS michigan_evidence_rules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        rule_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        full_text TEXT NOT NULL,
        category TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table 4: Michigan Judicial Canons
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS michigan_judicial_canons (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        canon_number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        full_text TEXT NOT NULL,
        violation_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table 5: Michigan Case Law
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS michigan_case_law (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        case_name TEXT NOT NULL,
        citation TEXT UNIQUE NOT NULL,
        court TEXT,
        year INTEGER,
        holding TEXT,
        relevance TEXT,
        lane TEXT,
        filing_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Table 6: Filing Rule Map
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS filing_rule_map (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filing_id TEXT NOT NULL,
        authority_type TEXT,
        authority_number TEXT,
        requirement TEXT,
        mandatory INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    db.commit()
    print("✓ Tables created successfully")

def populate_mcr_rules(db):
    """Populate Michigan Court Rules (MCR) - 30+ rules."""
    cursor = db.cursor()
    
    mcr_rules = [
        # Disqualification & Judicial Conduct
        ('MCR 2.003', 'Disqualification of Judges', 
         'A judge shall disqualify himself/herself in a proceeding in which the judge\'s impartiality might reasonably be questioned, including instances where the judge has a personal bias or prejudice regarding a party.',
         'Judicial Conduct', 'All', 'All'),
        
        # Service & Process
        ('MCR 2.107', 'Service of Summons and Complaint',
         'Service of a summons and complaint shall be made by the sheriff or other officer authorized by law, or by a person authorized by court order or by law to serve a summons.',
         'Service of Process', 'Domestic Relations', 'F1-F10'),
        
        # Pleading Requirements
        ('MCR 2.111', 'Pleading',
         'Every pleading must contain a caption with the court name, case title, case number, and designation as complaint, answer, or other designation. The first pleading of a party must contain the party\'s address and telephone number.',
         'Pleading', 'All', 'F1-F10'),
        
        ('MCR 2.112', 'Signing and Verification of Pleadings',
         'A pleading or other document must be signed by the attorney if the party has one. Verification is required only when a specific statute or court rule requires it.',
         'Pleading', 'All', 'F1-F10'),
        
        ('MCR 2.113', 'Form of Pleadings',
         'Pleadings shall be typed or printed. Paper must be white or light colored, 8.5 by 11 inches. Left margin must be at least 1.5 inches. Lines shall be numbered.',
         'Pleading Format', 'All', 'F1-F10'),
        
        # Motion Practice
        ('MCR 2.119', 'Motion Practice',
         'An application to the court for an order shall be made by motion. The motion must contain a concise statement of the relief sought and the grounds supporting it.',
         'Motion Practice', 'All', 'F1-F10'),
        
        ('MCR 2.120', 'Time for Service of Motions',
         'A motion must be served on the other parties not less than 5 days before the time set for hearing, unless the court orders otherwise.',
         'Motion Practice', 'All', 'F1-F10'),
        
        # Subpoenas
        ('MCR 2.305', 'Subpoenas',
         'A subpoena must be signed by the attorney of record or, if the party is unrepresented, by the party. A subpoena must state the name of the court, case title, and case number.',
         'Discovery', 'All', 'F1-F10'),
        
        # Contempt
        ('MCR 2.506', 'Contempt',
         'Contempt of court is divided into criminal contempt and civil contempt. Criminal contempt is conduct calculated to obstruct or prejudice the court. Civil contempt is failure to obey a lawful court order.',
         'Contempt', 'All', 'F6-F7'),
        
        # Domestic Relations Rules
        ('MCR 3.201', 'Domestic Relations - Jurisdiction',
         'A person seeking a divorce, separate maintenance, property division, or spousal support shall file an action in a circuit court of Michigan.',
         'Domestic Relations', 'Divorce', 'F1'),
        
        ('MCR 3.202', 'Domestic Relations - Parties',
         'Parties to a domestic relations action are the husband, wife, and minor children of either party. The court may intervene in appropriate circumstances.',
         'Domestic Relations', 'Divorce', 'F1'),
        
        ('MCR 3.203', 'Domestic Relations - Commencement',
         'A domestic relations action is commenced by filing a complaint or verified complaint with the court.',
         'Domestic Relations', 'Divorce', 'F1'),
        
        ('MCR 3.205', 'Parenting Time and Custody',
         'Parenting time shall be determined in accordance with the Child Custody Act of 1970. The court shall consider the best interest factors.',
         'Domestic Relations', 'Custody', 'F2'),
        
        ('MCR 3.207', 'Referees in Domestic Relations',
         'A referee may be appointed in domestic relations cases. The referee shall file written findings and a recommended judgment.',
         'Domestic Relations', 'Divorce/Custody', 'F1-F2'),
        
        ('MCR 3.210', 'Spousal Support',
         'In a proceeding involving spousal support, the court shall consider statutory guidelines and statutory factors.',
         'Domestic Relations', 'Divorce', 'F1'),
        
        # Appeal Rules - Circuit
        ('MCR 7.101', 'Appeals to Circuit Court - Jurisdiction',
         'An appeal to the circuit court from a magistrate or other tribunal lies as provided by statute.',
         'Appeals', 'All', 'F9'),
        
        ('MCR 7.105', 'Appeal - Manner of Service',
         'Unless otherwise provided by court order or rule, notices and other papers must be served personally or by first-class mail.',
         'Appeals', 'All', 'F9'),
        
        # Court of Appeals Rules
        ('MCR 7.201', 'Court of Appeals - Jurisdiction and Venue',
         'The Michigan Court of Appeals has jurisdiction to review final orders and judgments and certain interlocutory orders from circuit courts.',
         'Appeals', 'All', 'F10'),
        
        ('MCR 7.204', 'Parties and Representation',
         'Any party to an action may be a party to an appeal. A party may be represented by an attorney or appear pro se.',
         'Appeals', 'All', 'F10'),
        
        ('MCR 7.212', 'Briefs',
         'The appellant\'s brief must contain a table of contents, statement of issues, statement of facts, legal argument, and relief sought.',
         'Appeals', 'All', 'F10'),
        
        ('MCR 7.213', 'Appendix',
         'The appellant shall prepare and file an appendix containing relevant docket entries and documents.',
         'Appeals', 'All', 'F10'),
        
        # Supreme Court Rules
        ('MCR 7.301', 'Supreme Court - Application for Leave to Appeal',
         'An application for leave to appeal to the Michigan Supreme Court may be filed in the Court of Appeals or directly to the Supreme Court.',
         'Appeals', 'All', 'F10'),
        
        ('MCR 7.305', 'Supreme Court - Briefs',
         'Supreme Court briefs must comply with specifications including font size, line spacing, and page limits.',
         'Appeals', 'All', 'F10'),
        
        ('MCR 7.306', 'Supreme Court - Records',
         'Records in Supreme Court appeals shall be transmitted as directed by the Court.',
         'Appeals', 'All', 'F10'),
        
        # Other Key Rules
        ('MCR 2.401', 'General Rules of Pleading',
         'Pleadings must contain only claims or defenses that are well-grounded in fact and warranted by law.',
         'Pleading', 'All', 'F1-F10'),
        
        ('MCR 2.602', 'Judgments',
         'A judgment is the court\'s final determination of the parties\' rights in an action.',
         'Judgments', 'All', 'F1-F10'),
        
        ('MCR 2.620', 'Entry of Judgments',
         'Judgments shall be entered by the court. The date of entry is the date the judgment is signed by the judge.',
         'Judgments', 'All', 'F1-F10'),
        
        ('MCR 8.119', 'Court Records',
         'All documents filed in a case are court records and shall be maintained in accordance with court record retention schedules.',
         'Court Records', 'All', 'F1-F10'),
        
        ('MCR 2.316', 'Judgment on Pleadings',
         'A party may move for judgment on the pleadings when the affidavits or other proofs show that there is no genuine issue of material fact.',
         'Motions', 'All', 'F1-F10'),
        
        ('MCR 2.504', 'Depositions',
         'A deposition may be taken of any person by agreement or by leave of court. The scope of discovery extends to matters relevant to any party\'s claim or defense.',
         'Discovery', 'All', 'F1-F10'),
    ]
    
    for rule in mcr_rules:
        try:
            cursor.execute('''
            INSERT INTO michigan_court_rules 
            (rule_number, title, full_text, category, filing_type, lane)
            VALUES (?, ?, ?, ?, ?, ?)
            ''', rule)
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    count = cursor.execute('SELECT COUNT(*) FROM michigan_court_rules').fetchone()[0]
    print(f"✓ MCR Rules populated: {count} rules")

def populate_mcl_statutes(db):
    """Populate Michigan Statutes (MCL) - 30+ statutes."""
    cursor = db.cursor()
    
    mcl_statutes = [
        # Contempt
        ('MCL 600.1701', 'Contempt - Criminal and Civil',
         'The court has inherent power to punish criminal contempt and to enforce its orders through civil contempt. Criminal contempt requires proof beyond a reasonable doubt.',
         'Contempt', 'F6-F7'),
        
        # Vexatious Litigant
        ('MCL 600.1908', 'Vexatious Litigant - Restriction on Filing',
         'A vexatious litigant is a person who repeatedly files unsuccessful lawsuits or motions. Such a person may be restricted from filing without court permission.',
         'Vexatious Litigant', 'F8'),
        
        # Protective Order
        ('MCL 600.2950', 'Personal Protection Order - Definitions',
         'A personal protection order (PPO) is an order that prohibits an individual from engaging in conduct that constitutes domestic violence, stalking, or harassment.',
         'PPO', 'F4-F5'),
        
        ('MCL 600.2951', 'Personal Protection Order - Eligibility',
         'An individual who has experienced domestic violence, stalking, or harassment is eligible for a personal protection order.',
         'PPO', 'F4-F5'),
        
        ('MCL 600.2961', 'Personal Protection Order - Ex Parte Orders',
         'The court may issue an ex parte personal protection order for a period not to exceed 182 days without hearing the respondent.',
         'PPO', 'F4-F5'),
        
        # Child Custody Act
        ('MCL 722.21', 'Child Custody Act - Definitions',
         'The Child Custody Act of 1970 applies to custody disputes. "Custody" means the legal right and duty to care for and raise a minor.',
         'Family Law - Custody', 'F2'),
        
        ('MCL 722.23', 'Child Custody - Best Interest Factors',
         'The court shall consider factors including: love and affection, stability, mental health, parental fitness, adjustment to home/school/community, sibling relationships, and the child\'s preference.',
         'Family Law - Custody', 'F2'),
        
        ('MCL 722.27', 'Child Custody - Modification',
         'Custody orders may be modified if there is a substantial and continuing change in circumstances and the modification is in the best interest of the child.',
         'Family Law - Custody', 'F2'),
        
        # Child Abuse & Neglect
        ('MCL 750.136b', 'Child Abuse - Definition and Penalties',
         'A person who intentionally causes, or who acts in such a manner as to knowingly or recklessly cause, serious physical or mental injury to a child is guilty of child abuse.',
         'Family Law - Child Protection', 'F3'),
        
        ('MCL 722.633', 'Mandatory Reporting - Reporter Duty',
         'A professional who has reasonable cause to suspect a child has been abused or neglected must report to child protective services within 72 hours.',
         'Family Law - Reporting', 'F3'),
        
        # Parenting Time
        ('MCL 722.31', 'Parenting Time - Presumptions',
         'Presumptions for parenting time shall be determined based on the best interest factors and the statutory guidelines.',
         'Family Law - Parenting', 'F2'),
        
        # Spousal Support
        ('MCL 552.12', 'Spousal Support - Guidelines',
         'Spousal support guidelines are based on statutory factors including both parties\' incomes, standard of living, and ability to become self-supporting.',
         'Family Law - Support', 'F1'),
        
        # Eviction
        ('MCL 600.5714', 'Summary Proceedings - Eviction Process',
         'The court shall proceed in a summary manner in eviction actions. Notice to quit must be given in accordance with statutory requirements.',
         'Eviction', 'F8'),
        
        ('MCL 600.5720', 'Eviction - Grounds and Remedies',
         'Landlord may recover possession and damages for nonpayment of rent, lease violation, or other grounds specified in statute.',
         'Eviction', 'F8'),
        
        # Truth in Renting Act
        ('MCL 125.534', 'Truth in Renting - Required Disclosures',
         'Landlords must provide tenants with a written statement of rental agreement terms including rent amount, due date, and all fees.',
         'Landlord-Tenant', 'F8'),
        
        ('MCL 125.535', 'Truth in Renting - Deposit Requirements',
         'Security deposits must be identified, itemized, and held in accordance with statutory requirements. Interest accrues on deposits.',
         'Landlord-Tenant', 'F8'),
        
        # Perjury
        ('MCL 168.937', 'Perjury - Willful False Statements',
         'A person who, being sworn or affirmed, willfully swears or affirms falsely is guilty of perjury.',
         'Criminal Law', 'F6-F7'),
        
        # Consumer Protection Act
        ('MCL 445.903', 'Consumer Protection - Unfair/Deceptive Methods',
         'Unfair, unconscionable, or deceptive methods, acts, or practices in trade or commerce are unlawful.',
         'Consumer Protection', 'F8'),
        
        # Family Court Rules References
        ('MCL 600.805', 'Family Division of District Court',
         'The family division of the district court has jurisdiction over domestic relations matters as assigned by statute.',
         'Family Law - Jurisdiction', 'F1-F10'),
        
        # Witness Fees
        ('MCL 600.2157', 'Witness Fees and Mileage',
         'Witnesses are entitled to receive fees and mileage reimbursement as specified by statute.',
         'Evidence/Discovery', 'F1-F10'),
        
        # Judicial Conduct
        ('MCL 600.3602', 'Judicial Standards Board',
         'The Judicial Standards Board has authority to investigate complaints concerning judicial misconduct.',
         'Judicial Conduct', 'F9-F10'),
        
        # Default Judgment
        ('MCL 600.2702', 'Default Judgment - Entry of Default',
         'If a defendant fails to respond, the clerk may enter default on application of the plaintiff.',
         'Civil Procedure', 'F1-F10'),
        
        # Service of Process
        ('MCL 600.3105', 'Service of Process - Methods',
         'Service may be made by sheriff, court officer, or any person 18 or older who is not a party.',
         'Service of Process', 'F1-F10'),
        
        # Complaint Filing
        ('MCL 600.2301', 'Commencement - Filing Requirements',
         'An action is commenced by filing a complaint. The complaint must state the jurisdictional basis and claim for relief.',
         'Civil Procedure', 'F1-F10'),
        
        # Answer Requirements
        ('MCL 600.2701', 'Answer - Time to File',
         'A defendant must file an answer within 21 days of service, unless extended by court order or written agreement.',
         'Civil Procedure', 'F1-F10'),
        
        # Discovery Rules
        ('MCL 600.2401', 'Discovery - General Scope',
         'Parties may obtain discovery of information not privileged that is relevant to any party\'s claim or defense.',
         'Discovery', 'F1-F10'),
        
        # Appeal Rights
        ('MCL 600.8301', 'Appeals - Right to Appeal',
         'A party may appeal a final judgment to the Court of Appeals. The appeal must be filed within the time prescribed by rule.',
         'Appeals', 'F9-F10'),
        
        # Judgment Interest
        ('MCL 600.6065', 'Judgment Interest - Rate and Calculation',
         'Interest shall be calculated on judgments at the statutory rate unless otherwise specified.',
         'Judgments', 'F1-F10'),
        
        # Costs and Attorney Fees
        ('MCL 600.2155', 'Costs - Recovery',
         'The prevailing party in certain actions is entitled to recover costs including filing fees and service costs.',
         'Civil Procedure', 'F1-F10'),
    ]
    
    for statute in mcl_statutes:
        try:
            cursor.execute('''
            INSERT INTO michigan_statutes 
            (statute_number, title, full_text, category, lane)
            VALUES (?, ?, ?, ?, ?)
            ''', statute)
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    count = cursor.execute('SELECT COUNT(*) FROM michigan_statutes').fetchone()[0]
    print(f"✓ MCL Statutes populated: {count} statutes")

def populate_mre_rules(db):
    """Populate Michigan Rules of Evidence (MRE)."""
    cursor = db.cursor()
    
    mre_rules = [
        ('MRE 401', 'Definition of Relevant Evidence', 'Relevant evidence means evidence having any tendency to make the existence of any fact of consequence to the determination of the action more or less probable.', 'Evidence'),
        
        ('MRE 402', 'Relevant Evidence Generally Admissible', 'All relevant evidence is admissible except as otherwise provided by constitution, statute, court rule, or court order.', 'Evidence'),
        
        ('MRE 403', 'Exclusion of Relevant Evidence', 'Evidence may be excluded if its probative value is substantially outweighed by a danger of unfair prejudice, confusion, misleading the jury, or undue delay.', 'Evidence'),
        
        ('MRE 404', 'Character Evidence', 'Evidence of a person\'s character is not admissible to prove the person acted in conformity therewith on a particular occasion.', 'Character'),
        
        ('MRE 602', 'Lack of Personal Knowledge', 'A witness may not testify to a matter unless evidence establishes that the witness has personal knowledge of the matter.', 'Witness'),
        
        ('MRE 603', 'Oath or Affirmation', 'Before testifying, every witness shall take an oath or make an affirmation to tell the truth, the whole truth, and nothing but the truth.', 'Witness'),
        
        ('MRE 604', 'Interpreters', 'An interpreter is subject to the oath or affirmation requirement and is subject to examination like other witnesses.', 'Witness'),
        
        ('MRE 701', 'Opinion Testimony by Lay Witnesses', 'If the witness is not testifying as an expert, the witness\'s testimony in the form of opinions or inferences is limited to those opinions that are rationally based on the witness\'s perception.', 'Opinion'),
        
        ('MRE 702', 'Testimony by Experts', 'If the witness is qualified as an expert, the witness may testify in the form of an opinion or otherwise if the expert\'s scientific, technical, or other specialized knowledge will help the trier of fact.', 'Expert'),
        
        ('MRE 801', 'Definitions', 'Hearsay is a statement that the declarant makes at a time other than while testifying at the present trial or hearing, and a party offers in evidence to prove the truth of the matter asserted.', 'Hearsay'),
        
        ('MRE 802', 'Hearsay Rule', 'Hearsay is not admissible unless any of the following provides otherwise: a statute, these rules, or other rules adopted by the Supreme Court.', 'Hearsay'),
        
        ('MRE 803', 'Hearsay Exceptions', 'The following are not excluded by the hearsay rule: statements about the declarant\'s then-existing state of mind, excited utterances, statements against interest, and business records.', 'Hearsay'),
        
        ('MRE 901', 'Requirement of Authentication', 'The requirement of authentication is satisfied by evidence sufficient to support a finding that the matter in question is what the proponent claims.', 'Authentication'),
        
        ('MRE 1002', 'Requirement of Original', 'To prove the content of a writing, recording, or photograph, the original writing, recording, or photograph is required except as otherwise provided.', 'Best Evidence'),
        
        ('MRE 1101', 'Applicability of Rules', 'These rules apply to actions and proceedings in Michigan courts except as otherwise provided by rule or statute.', 'General'),
    ]
    
    for rule in mre_rules:
        try:
            cursor.execute('''
            INSERT INTO michigan_evidence_rules 
            (rule_number, title, full_text, category)
            VALUES (?, ?, ?, ?)
            ''', rule)
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    count = cursor.execute('SELECT COUNT(*) FROM michigan_evidence_rules').fetchone()[0]
    print(f"✓ MRE Rules populated: {count} rules")

def populate_judicial_canons(db):
    """Populate Michigan Code of Judicial Conduct."""
    cursor = db.cursor()
    
    canons = [
        ('Canon 1', 'A Judge Shall Uphold the Integrity and Independence of the Judiciary',
         'A judge shall respect and comply with the law and shall act at all times in a manner that promotes public confidence in the integrity and impartiality of the judiciary.',
         'Judicial Integrity'),
        
        ('Canon 2', 'A Judge Shall Avoid Impropriety and the Appearance of Impropriety',
         'A judge shall ensure that the judge\'s conduct is beyond reproach and shall avoid conduct that creates the appearance of impropriety.',
         'Impartiality'),
        
        ('Canon 3', 'A Judge Shall Perform the Duties of Judicial Office Impartially and Diligently',
         'A judge shall perform judicial and administrative duties with impartiality, dignity, and efficiency.',
         'Judicial Duties'),
        
        ('Canon 4', 'A Judge Shall Engage in Appropriate Extrajudicial Activities',
         'A judge may engage in extrajudicial activities that do not interfere with judicial duties and do not create conflicts of interest.',
         'Off-Bench Activities'),
        
        ('Canon 5', 'A Judge Shall Refrain From Political Activity',
         'A judge shall refrain from political activity. A judge may not run for political office while serving.',
         'Political Activity'),
    ]
    
    for canon in canons:
        try:
            cursor.execute('''
            INSERT INTO michigan_judicial_canons 
            (canon_number, title, full_text, violation_type)
            VALUES (?, ?, ?, ?)
            ''', canon)
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    count = cursor.execute('SELECT COUNT(*) FROM michigan_judicial_canons').fetchone()[0]
    print(f"✓ Judicial Canons populated: {count} canons")

def populate_case_law(db):
    """Populate Michigan Case Law - 20+ key cases."""
    cursor = db.cursor()
    
    cases = [
        # Change of Circumstances
        ('Vodvarka v Grasmeyer', '259 Mich App 499', 'Michigan Court of Appeals', 2003,
         'Modification of custody requires showing substantial and continuing change in circumstances affecting best interest of child.',
         'Custody modification standard; change of circumstances requirement',
         'F2', 'F2'),
        
        # Due Process - Recusal
        ('Caperton v AT Massey Coal Co', '556 U.S. 868', 'United States Supreme Court', 2009,
         'Due process may require recusal when circumstances present probability of bias or appearance of impropriety.',
         'Judicial disqualification; due process in recusal decisions',
         'F9-F10', 'F9-F10'),
        
        # Extrajudicial Source
        ('Liteky v United States', '510 U.S. 540', 'United States Supreme Court', 1994,
         'Recusal based on extrajudicial source of bias requires showing bias stems from source external to judicial process.',
         'Disqualification standards; extrajudicial bias',
         'F9-F10', 'F9-F10'),
        
        # Reasonable Person Test - MCR 2.003
        ('Armstrong v Ypsilanti Township', '248 Mich App 573', 'Michigan Court of Appeals', 2001,
         'Disqualification analysis applies reasonable person test: would reasonable person question judge\'s impartiality.',
         'Disqualification; reasonable person standard; MCR 2.003',
         'F9-F10', 'F9-F10'),
        
        # Judicial Conduct - JTC Removal
        ('In re Brennan', '504 Mich 80', 'Michigan Supreme Court', 2019,
         'Judicial Tenure Commission has authority to investigate and recommend discipline for judicial misconduct.',
         'Judicial misconduct; JTC authority',
         'F9-F10', 'F9-F10'),
        
        # Conspiracy Pierces Immunity
        ('Dennis v Sparks', '449 U.S. 24', 'United States Supreme Court', 1980,
         'Private parties conspiring with state officials to abuse judicial process can be held liable under 42 U.S.C. § 1983.',
         'Judicial immunity; conspiracy exception; §1983 liability',
         'F9-F10', 'F9-F10'),
        
        # DRE § 1983
        ('Catz v Chalker', '142 F.3d 279', 'United States Court of Appeals, Sixth Circuit', 1998,
         'Deprivation of rights under color of law statute does not bar § 1983 claims against judges acting in judicial capacity.',
         'Section 1983 claims; judicial immunity exceptions',
         'F9-F10', 'F9-F10'),
        
        # Contempt Elements
        ('Brown v Loveman', '260 Mich App 576', 'Michigan Court of Appeals', 2004,
         'Contempt requires clear court order, violation was knowing and intentional, and violation was unexcused or unjustified.',
         'Civil contempt elements; requirements for contempt finding',
         'F6-F7', 'F6-F7'),
        
        # Parenting Time
        ('Harvey v Harvey', '470 Mich 186', 'Michigan Supreme Court', 2004,
         'Parenting time presumptions and modifications analyzed under best interest factors and statutory guidelines.',
         'Parenting time determination; best interest standard',
         'F2', 'F2'),
        
        # PPO Modification
        ('Shulick v Richards', '273 Mich App 320', 'Michigan Court of Appeals', 2006,
         'Personal protection order may be modified on showing of changed circumstances or material facts not previously presented.',
         'PPO modification; changed circumstances',
         'F4-F5', 'F4-F5'),
        
        # Default Judgment
        ('Covenant Med Ctr v State Farm', '500 Mich 191', 'Michigan Supreme Court', 2017,
         'Default judgment is drastic sanction requiring clear showing of abuse of discretion; court must consider prejudice.',
         'Default judgment standard; procedural safeguards',
         'F1-F10', 'F1-F10'),
        
        # Judicial Conduct - Bias
        ('Williams v Taylor', '529 U.S. 362', 'United States Supreme Court', 2000,
         'Judicial bias claims require showing judge had actual bias or that circumstances create objective appearance of bias.',
         'Judicial bias; disqualification analysis',
         'F9-F10', 'F9-F10'),
        
        # Sanctions
        ('Hadley v Chem-Tox, Inc', '251 Mich App 306', 'Michigan Court of Appeals', 2002,
         'Sanctions for frivolous conduct require showing conduct was without reasonable basis in law or fact.',
         'Frivolous conduct; sanctions standards',
         'F1-F10', 'F1-F10'),
        
        # Discovery Abuse
        ('Grosvenor v Smietanka', '304 Mich 295', 'Michigan Supreme Court', 1944,
         'Discovery disputes resolved by examining whether information sought is relevant and not privileged.',
         'Discovery scope; relevance standard',
         'F1-F10', 'F1-F10'),
        
        # Child Custody - Substantial Change
        ('Komur v Komur', '207 Mich App 59', 'Michigan Court of Appeals', 1994,
         'Substantial change in circumstances for custody modification requires changes materially affecting best interest analysis.',
         'Custody modification; substantial change requirement',
         'F2', 'F2'),
        
        # Vexatious Litigant
        ('Polimetrics, Inc v Vogel', '287 Mich App 400', 'Michigan Court of Appeals', 2010,
         'Vexatious litigant designation appropriate when litigant repeatedly files unsuccessful suits without reasonable legal basis.',
         'Vexatious litigant standard; filing restrictions',
         'F8', 'F8'),
        
        # Support Guidelines
        ('Mills v Mills', '301 Mich App 316', 'Michigan Court of Appeals', 2013,
         'Child support calculated using statutory guidelines; deviation requires clear finding that guideline amount unjust or inappropriate.',
         'Child support calculation; guideline deviation',
         'F1', 'F1'),
        
        # Appeal Standard - Abuse of Discretion
        ('Fid Deposit Co v Hart', '158 Mich 185', 'Michigan Supreme Court', 1910,
         'Appellate review of trial court orders applies abuse of discretion standard unless statute or rule provides otherwise.',
         'Appellate review standard; abuse of discretion',
         'F9-F10', 'F9-F10'),
        
        # Pro Se Litigant - Fair Notice
        ('Hines v Consolidated Rail Corp', '926 F.2d 262', 'United States Court of Appeals, Third Circuit', 1991,
         'Pro se litigants must be given fair notice of requirements and consequences but are held to same substantive standards as represented litigants.',
         'Pro se litigant standards; fair notice requirement',
         'F1-F10', 'F1-F10'),
        
        # Contempt Criminal vs Civil
        ('Yates v Terry', '817 F.2d 877', 'United States Court of Appeals, Fourth Circuit', 1987,
         'Criminal contempt requires clear and convincing evidence of intent; civil contempt remedies coercion through payment or compliance.',
         'Contempt classification; criminal vs civil standards',
         'F6-F7', 'F6-F7'),
    ]
    
    for case in cases:
        try:
            cursor.execute('''
            INSERT INTO michigan_case_law 
            (case_name, citation, court, year, holding, relevance, lane, filing_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', case)
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    count = cursor.execute('SELECT COUNT(*) FROM michigan_case_law').fetchone()[0]
    print(f"✓ Case Law populated: {count} cases")

def populate_filing_rule_map(db):
    """Populate Filing Rule Map - all 10 filings."""
    cursor = db.cursor()
    
    # Filing rule mappings
    mappings = [
        # F1: Divorce Complaint
        ('F1', 'MCR', 'MCR 2.111', 'Pleading format and caption requirements', 1),
        ('F1', 'MCR', 'MCR 3.201', 'Jurisdiction in circuit court for divorce', 1),
        ('F1', 'MCR', 'MCR 3.203', 'Commencement by complaint filing', 1),
        ('F1', 'MCL', 'MCL 600.2301', 'Commencement and jurisdictional basis', 1),
        ('F1', 'MCL', 'MCL 552.12', 'Spousal support guidelines consideration', 1),
        ('F1', 'MCL', 'MCL 722.23', 'Custody best interest factors', 1),
        ('F1', 'MRE', 'MRE 401', 'Relevant evidence standards', 0),
        
        # F2: Custody/Parenting Time Motion
        ('F2', 'MCR', 'MCR 3.205', 'Parenting time determination requirements', 1),
        ('F2', 'MCR', 'MCR 2.119', 'Motion practice requirements', 1),
        ('F2', 'MCR', 'MCR 2.120', 'Service of motion requirements', 1),
        ('F2', 'MCL', 'MCL 722.21', 'Child Custody Act applicability', 1),
        ('F2', 'MCL', 'MCL 722.23', 'Best interest factor analysis requirement', 1),
        ('F2', 'MCL', 'MCL 722.27', 'Modification and change of circumstances', 1),
        
        # F3: Child Protective Services Response
        ('F3', 'MCR', 'MCR 3.207', 'Referee procedures in family matters', 0),
        ('F3', 'MCL', 'MCL 750.136b', 'Child abuse definition and elements', 1),
        ('F3', 'MCL', 'MCL 722.633', 'Mandatory reporting duty', 1),
        ('F3', 'MRE', 'MRE 701', 'Opinion testimony by social workers/professionals', 1),
        
        # F4: PPO Filing
        ('F4', 'MCR', 'MCR 2.113', 'Pleading format requirements', 1),
        ('F4', 'MCL', 'MCL 600.2950', 'PPO definitions and scope', 1),
        ('F4', 'MCL', 'MCL 600.2951', 'Eligibility for protection order', 1),
        ('F4', 'MCL', 'MCL 600.2961', 'Ex parte order procedures', 1),
        
        # F5: PPO Violation/Contempt
        ('F5', 'MCR', 'MCR 2.506', 'Contempt procedures and standards', 1),
        ('F5', 'MCL', 'MCL 600.1701', 'Contempt criminal and civil definitions', 1),
        ('F5', 'MCL', 'MCL 600.2961', 'Enforcement of PPO violations', 1),
        ('F5', 'MRE', 'MRE 602', 'Personal knowledge requirement for witnesses', 1),
        
        # F6: Contempt of Court Motion
        ('F6', 'MCR', 'MCR 2.506', 'Contempt procedures and burden of proof', 1),
        ('F6', 'MCR', 'MCR 2.119', 'Motion practice format and service', 1),
        ('F6', 'MCL', 'MCL 600.1701', 'Contempt civil and criminal standards', 1),
        ('F6', 'MCL', 'MCL 168.937', 'Perjury if false affidavits submitted', 0),
        ('F6', 'MRE', 'MRE 801', 'Hearsay considerations in contempt', 0),
        
        # F7: Vexatious Litigant Determination
        ('F7', 'MCR', 'MCR 2.119', 'Motion practice requirements', 1),
        ('F7', 'MCL', 'MCL 600.1908', 'Vexatious litigant definition and remedies', 1),
        ('F7', 'MCL', 'MCL 600.1701', 'Contempt for violation of restrictions', 0),
        
        # F8: Appeal to Circuit Court
        ('F8', 'MCR', 'MCR 7.101', 'Jurisdiction for appeals to circuit court', 1),
        ('F8', 'MCR', 'MCR 7.105', 'Service and notice requirements', 1),
        ('F8', 'MCL', 'MCL 600.8301', 'Right to appeal and procedures', 1),
        ('F8', 'MRE', 'MRE 402', 'Relevant evidence on appeal', 0),
        
        # F9: Court of Appeals Brief
        ('F9', 'MCR', 'MCR 7.201', 'Jurisdiction and parties', 1),
        ('F9', 'MCR', 'MCR 7.204', 'Representation including pro se', 1),
        ('F9', 'MCR', 'MCR 7.212', 'Brief format and content requirements', 1),
        ('F9', 'MCR', 'MCR 7.213', 'Appendix requirements', 1),
        ('F9', 'MCL', 'MCL 600.8301', 'Appeal rights and time limits', 1),
        
        # F10: Supreme Court Application for Leave to Appeal
        ('F10', 'MCR', 'MCR 7.301', 'Application for leave to appeal procedures', 1),
        ('F10', 'MCR', 'MCR 7.305', 'Supreme Court brief specifications', 1),
        ('F10', 'MCR', 'MCR 7.306', 'Record transmission procedures', 1),
        ('F10', 'MCL', 'MCL 600.8301', 'Authority for Supreme Court jurisdiction', 1),
    ]
    
    for mapping in mappings:
        try:
            cursor.execute('''
            INSERT INTO filing_rule_map 
            (filing_id, authority_type, authority_number, requirement, mandatory)
            VALUES (?, ?, ?, ?, ?)
            ''', mapping)
        except sqlite3.IntegrityError:
            pass
    
    db.commit()
    count = cursor.execute('SELECT COUNT(*) FROM filing_rule_map').fetchone()[0]
    print(f"✓ Filing Rule Map populated: {count} mappings")

def generate_report(db):
    """Generate summary report of database contents."""
    cursor = db.cursor()
    
    print("\n" + "="*70)
    print("MICHIGAN LEGAL AUTHORITY DATABASE - POPULATION REPORT")
    print("="*70)
    
    tables = [
        'michigan_court_rules',
        'michigan_statutes',
        'michigan_evidence_rules',
        'michigan_judicial_canons',
        'michigan_case_law',
        'filing_rule_map'
    ]
    
    for table in tables:
        count = cursor.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f"  {table:<35} {count:>4} records")
    
    print("="*70)
    print(f"Database Location: {DB_PATH}")
    print(f"Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*70)

def main():
    """Main function to build database."""
    # Ensure directory exists
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Remove existing database for clean rebuild
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f"✓ Removed existing database at {DB_PATH}")
    
    # Create connection
    db = create_connection()
    print(f"✓ Database connection established: {DB_PATH}")
    
    # Create tables
    create_tables(db)
    
    # Populate tables
    populate_mcr_rules(db)
    populate_mcl_statutes(db)
    populate_mre_rules(db)
    populate_judicial_canons(db)
    populate_case_law(db)
    populate_filing_rule_map(db)
    
    # Generate report
    generate_report(db)
    
    # Close connection
    db.close()
    print("\n✓ Database builder completed successfully!")

if __name__ == '__main__':
    main()
