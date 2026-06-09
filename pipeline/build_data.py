#!/usr/bin/env python3
"""
Industry Risk Radar - data builder (v2, radar layout contract).
Reference implementation of methodology.md v2.0.

Emits public/data.js (window.__RISK_DATA__) and public/data.json (canonical).

Contract (matches the layout's app.js):
  current_month, data_mode, categories_meta:[{key,label}],
  months:{ 'YYYY-MM': { label, live_sector, industries:[...], regulatory:{...} } }
  industry: { key,label,sector_note,band,risk_score,delta,seed,sentiment_neg,volume_total,
              categories:[{key,label,score,volume,band}], trend:{weeks,values}, events:[...] }

PROTOTYPE run: Automotive uses REAL Signal data (pulled 2026-06-09) across all 8 themes.
Other 9 sectors use clearly-flagged sample data (seed:true). Per-theme negativity and event
severity for Automotive use documented estimates where a live sentiment/events pull would be
substituted; volumes and trends are real. Regulatory items are illustrative samples.
"""
import json, math, random, os, datetime
random.seed(7)

WEEKS = ['2026-03-16','2026-03-23','2026-03-30','2026-04-06','2026-04-13','2026-04-20',
         '2026-04-27','2026-05-04','2026-05-11','2026-05-18','2026-05-25','2026-06-01']

CATS = [
  ('regulatory','Regulatory & legal'), ('financial','Financial & market'),
  ('operational','Operational & supply'), ('cyber','Cyber & data'),
  ('environmental','Environmental & climate'), ('governance','Governance & ethics'),
  ('product','Product & safety'), ('labor','Labour & workforce'),
]
NEG = {'regulatory':0.42,'financial':0.55,'operational':0.48,'cyber':0.70,
       'environmental':0.50,'governance':0.66,'product':0.72,'labor':0.52}

def band(s): return 'high' if s>=80 else 'elevated' if s>=60 else 'moderate' if s>=40 else 'low'
def clamp(v,a,b): return max(a,min(b,v))

# ---- methodology v2 component scores (per theme) ----
def vol_momentum(weekly):
    recent = sum(weekly[-5:])/5.0
    base = sum(weekly)/len(weekly)
    ratio = recent/base if base else 1.0
    return clamp((ratio-0.5)*100, 0, 100)
def event_severity(mag):
    return clamp(20*math.log10(1+mag), 0, 100) if mag else 0.0
def theme_score(weekly, neg, mag):
    return round(0.40*vol_momentum(weekly) + 0.35*neg*100 + 0.25*event_severity(mag))

# ===================== REAL AUTOMOTIVE DATA (Signal, 2026-06-09) =====================
# per-topic weekly article_count (12 full weeks), grouped into the 8 themes
AUTO_TOPICS = {
 'regulatory': [
   [9672,10111,9099,9148,11295,9273,11006,10829,11049,10087,8681,8702],  # Regulation
   [17,86,27,52,40,33,55,16,133,19,23,5]],                               # Antitrust Laws
 'financial': [
   [421,203,209,121,164,171,3292,1579,2136,267,314,108],                 # Profit Warnings
   [102,155,47,78,56,34,227,286,57,68,104,62],                           # International Trade
   [0,0,1,0,3,0,0,0,0,0,0,0]],                                           # Accounting Irregularities
 'operational': [
   [6269,8066,6189,6679,7263,6742,7155,5768,6771,7351,5345,5447],        # Supply Chain
   [1002,681,1358,766,701,561,876,1653,270,533,464,447]],                # Supply Chain Disruptions
 'cyber': [
   [31,75,97,37,14,9,48,7,74,18,13,6],                                   # Cyber Attack
   [5,86,15,13,8,26,22,78,6,7,25,3]],                                    # Cyber Security
 'environmental': [
   [383,689,425,352,374,302,341,325,387,321,434,462],                    # Climate change
   [4420,4943,5049,4400,5013,4800,4158,4424,5451,4490,4404,5618],        # Carbon Emissions
   [510,364,511,572,502,579,446,550,765,614,442,1039]],                  # Air Pollution
 'governance': [
   [11331,10967,10072,12350,12851,17911,10518,10570,14181,10238,9259,9930], # Corporate Controversy
   [10513,12844,10180,10610,12359,11295,12966,12959,15321,9795,9023,9982],  # Corporate Crisis
   [516,313,187,109,219,350,305,194,217,246,206,170],                       # Corporate Litigation
   [231,189,423,177,691,341,196,285,361,192,207,241]],                      # Fraud
 'product': [
   [3039,4005,2871,4642,4540,3217,2830,3171,3662,3268,3529,4563],        # Product Recall
   [691,1323,1309,629,1155,1261,858,610,724,819,879,1021]],              # Reliability and Safety
 'labor': [
   [125,78,57,80,86,70,50,107,90,305,141,381],                          # Strikes
   [418,131,234,140,441,320,572,1083,1151,444,220,57]],                 # Corporate Downsizing
}
# real automotive events -> magnitudes (peak_mean_ratio) + theme tags
AUTO_EVENT_MAG = {'product':13200,'regulatory':13200,'governance':4140}
AUTO_EVENTS = [
 {'title':'3,700 Waymo vehicles recalled over software issue','magnitude':13200,'date':'2026-05-12','sources':442,'stories':112,'entities':['Waymo','NHTSA'],'categories':['product','regulatory'],'article_id':'445abde8-9ee5-3e3c-a3f1-d47e7ea8a489'},
 {'title':'Subaru recalls nearly 70K vehicles over affected models','magnitude':5610,'date':'2026-06-04','sources':192,'stories':8,'entities':['Subaru'],'categories':['product'],'article_id':'bf5ef7fe-747d-3946-bc34-4996388f3fb1'},
 {'title':'Toyota recalls 81K cars as dashboard failure hides safety alerts','magnitude':4650,'date':'2026-06-02','sources':155,'stories':3,'entities':['Toyota'],'categories':['product'],'article_id':'f8134cab-5c5a-373f-b3c6-cf2c9b8facf4'},
 {'title':'Stellantis to recall 419,000 US vehicles over side air bag deployment','magnitude':4290,'date':'2026-05-21','sources':205,'stories':97,'entities':['Stellantis'],'categories':['product'],'article_id':'91b0e062-0781-3633-92d2-117d33269e6a'},
 {'title':'Ford recalls vehicles after roofs can detach at highway speeds','magnitude':4260,'date':'2026-05-19','sources':142,'stories':4,'entities':['Ford'],'categories':['product'],'article_id':'44a3e2e9-f402-3d45-9bee-8fe8511d9560'},
]

def build_automotive():
    cats, weekly_total = [], [0]*12
    for key,label in CATS:
        topic_arrays = AUTO_TOPICS[key]
        weekly = [sum(t[i] for t in topic_arrays) for i in range(12)]
        for i in range(12): weekly_total[i]+=weekly[i]
        vol = sum(weekly[-5:])  # trailing ~30d
        mag = AUTO_EVENT_MAG.get(key,0)
        sc = clamp(theme_score(weekly, NEG[key], mag), 3, 99)
        cats.append({'key':key,'label':label,'score':sc,'volume':int(vol),'band':band(sc)})
    num=sum(c['score']*c['volume'] for c in cats); den=sum(c['volume'] for c in cats)
    irs=round(num/den)
    neg=round(sum(NEG[c['key']]*c['volume'] for c in cats)/den,2)
    return {'key':'automotive','label':'Automotive','sector_note':'OEMs, EV makers, suppliers, mobility',
            'risk_score':irs,'delta':6,'seed':False,'sentiment_neg':neg,
            'volume_total':sum(c['volume'] for c in cats),'band':band(irs),
            'categories':cats,'trend':{'weeks':WEEKS,'values':weekly_total},'events':AUTO_EVENTS}

# ===================== SAMPLE SECTORS (flagged seed:true) =====================
PROFILE = {
 'energy':{'regulatory':78,'financial':55,'operational':70,'cyber':50,'environmental':90,'governance':52,'product':44,'labor':48},
 'finance':{'regulatory':82,'financial':76,'operational':48,'cyber':74,'environmental':32,'governance':70,'product':38,'labor':42},
 'fmcg':{'regulatory':48,'financial':50,'operational':64,'cyber':40,'environmental':58,'governance':46,'product':70,'labor':55},
 'healthcare':{'regulatory':80,'financial':46,'operational':54,'cyber':48,'environmental':36,'governance':64,'product':75,'labor':40},
 'media':{'regulatory':66,'financial':48,'operational':36,'cyber':58,'environmental':26,'governance':60,'product':34,'labor':44},
 'professional_services':{'regulatory':58,'financial':50,'operational':34,'cyber':54,'environmental':28,'governance':62,'product':30,'labor':40},
 'retail':{'regulatory':40,'financial':58,'operational':62,'cyber':52,'environmental':46,'governance':42,'product':50,'labor':64},
 'technology':{'regulatory':74,'financial':54,'operational':40,'cyber':84,'environmental':30,'governance':62,'product':46,'labor':46},
 'travel':{'regulatory':60,'financial':52,'operational':72,'cyber':46,'environmental':50,'governance':44,'product':66,'labor':62},
}
META = {
 'energy':('Energy','Oil, gas, power, utilities, renewables',184200,4),
 'finance':('Finance','Banks, insurers, asset managers, fintech',211400,-3),
 'fmcg':('FMCG','Food, beverage, household, personal care',142100,-2),
 'healthcare':('Healthcare','Pharma, providers, medtech, biotech',121300,2),
 'media':('Media','Broadcast, publishing, streaming, platforms',98600,3),
 'professional_services':('Professional Services','Consulting, legal, audit, advisory',74300,1),
 'retail':('Retail','Grocers, apparel, e-commerce',142100,-5),
 'technology':('Technology','Software, hardware, platforms, AI',268900,9),
 'travel':('Travel','Airlines, hotels, OTAs, tourism',98600,7),
}
SAMPLE_EVENTS = {
 'energy':[{'title':'Regulator opens probe into grid-failure disclosures','magnitude':1840,'date':'2026-05-28','sources':612,'stories':140,'entities':['National Grid','Ofgem'],'categories':['regulatory','operational'],'article_id':''},
           {'title':'Court orders major emitter to accelerate decarbonisation','magnitude':1210,'date':'2026-05-19','sources':503,'stories':90,'entities':['Shell'],'categories':['environmental','regulatory'],'article_id':''}],
 'finance':[{'title':'Conduct authority fines lender over mis-sold products','magnitude':1520,'date':'2026-05-26','sources':488,'stories':80,'entities':['FCA'],'categories':['regulatory','governance'],'article_id':''},
            {'title':'Credential-stuffing wave hits mobile banking apps','magnitude':1100,'date':'2026-05-14','sources':357,'stories':55,'entities':[],'categories':['cyber'],'article_id':''}],
 'fmcg':[{'title':'Food brand recalls product over contamination','magnitude':980,'date':'2026-06-01','sources':260,'stories':40,'entities':[],'categories':['product','operational'],'article_id':''}],
 'healthcare':[{'title':'Agency flags safety signal for blockbuster therapy','magnitude':1390,'date':'2026-05-24','sources':512,'stories':60,'entities':['FDA'],'categories':['product','regulatory'],'article_id':''}],
 'media':[{'title':'Platform faces scrutiny over content-moderation rules','magnitude':760,'date':'2026-05-27','sources':210,'stories':35,'entities':[],'categories':['regulatory','governance'],'article_id':''}],
 'professional_services':[{'title':'Consultancy faces audit-quality investigation','magnitude':640,'date':'2026-05-19','sources':150,'stories':18,'entities':[],'categories':['governance','regulatory'],'article_id':''}],
 'retail':[{'title':'Retailer breach exposes customer payment data','magnitude':1120,'date':'2026-05-31','sources':340,'stories':60,'entities':[],'categories':['cyber'],'article_id':''}],
 'technology':[{'title':'Antitrust suit targets platform bundling practices','magnitude':1980,'date':'2026-05-27','sources':690,'stories':120,'entities':['DOJ'],'categories':['regulatory','governance'],'article_id':''},
               {'title':'Zero-day exploit hits widely used enterprise stack','magnitude':1520,'date':'2026-05-13','sources':540,'stories':80,'entities':[],'categories':['cyber'],'article_id':''}],
 'travel':[{'title':'Safety regulator grounds fleet pending inspections','magnitude':2080,'date':'2026-05-30','sources':741,'stories':100,'entities':['FAA'],'categories':['product','regulatory'],'article_id':''}],
}
def sample_sector(key):
    label,note,vol_total,delta = META[key]
    prof=PROFILE[key]; mom=1.0+(delta/40.0)
    cats=[]; weekly_total=[0]*12
    for ck,cl in CATS:
        base=prof[ck]
        sc=clamp(round(base*(0.95+0.1*random.random())),3,99)
        vol=int(vol_total*(base/sum(prof.values()))*(0.8+0.4*random.random()))
        cats.append({'key':ck,'label':cl,'score':sc,'volume':vol,'band':band(sc)})
        for i in range(12):
            m = mom if i>=7 else 1.0
            weekly_total[i]+=int(vol/5*m*(0.8+0.4*random.random()))
    den=sum(c['volume'] for c in cats) or 1
    irs=round(sum(c['score']*c['volume'] for c in cats)/den)
    neg=round(sum(NEG[c['key']]*c['volume'] for c in cats)/den,2)
    return {'key':key,'label':label,'sector_note':note,'risk_score':irs,'delta':delta,'seed':True,
            'sentiment_neg':neg,'volume_total':sum(c['volume'] for c in cats),'band':band(irs),
            'categories':cats,'trend':{'weeks':WEEKS,'values':weekly_total},'events':SAMPLE_EVENTS.get(key,[])}

# ===================== REGULATORY (web-sourced, human-reviewed; samples here) =====================
REG = {
 'automotive':[
   {'name':'EU Battery Passport traceability mandate','jurisdiction':'EU','window':'3-6m','effective_date':'2026-09','summary':'EV batteries require a digital passport covering provenance, carbon footprint and recyclability.','source':'https://eur-lex.europa.eu'},
   {'name':'EU General Safety Regulation II — mandatory ADAS','jurisdiction':'EU','window':'3-6m','effective_date':'2026-09','summary':'New driver-assistance systems become mandatory on all new vehicle types.','source':'https://eur-lex.europa.eu'},
   {'name':'US NHTSA automatic emergency braking rule','jurisdiction':'US','window':'6-12m','effective_date':'2027-02','summary':'Phase-in deadline for AEB performance standards on light vehicles.','source':'https://www.nhtsa.gov'}],
 'energy':[
   {'name':'EU methane-emissions monitoring rules','jurisdiction':'EU','window':'3-6m','effective_date':'2026-09','summary':'Mandatory leak-detection and reporting for upstream operators.','source':'https://energy.ec.europa.eu'},
   {'name':'Carbon border adjustment — definitive phase','jurisdiction':'EU','window':'6-12m','effective_date':'2027-01','summary':'Importers of carbon-intensive goods begin paying the adjustment in full.','source':'https://taxation-customs.ec.europa.eu'}],
 'finance':[
   {'name':'EU DORA supervisory testing milestone','jurisdiction':'EU','window':'3-6m','effective_date':'2026-09','summary':'Digital Operational Resilience Act testing requirements take effect.','source':'https://www.eiopa.europa.eu'},
   {'name':'Basel III endgame — output floor step-up','jurisdiction':'Global','window':'6-12m','effective_date':'2027-01','summary':'Higher capital floors phase in, reshaping risk-weight modelling.','source':'https://www.bis.org'}],
 'healthcare':[
   {'name':'EU Joint Clinical Assessment framework','jurisdiction':'EU','window':'3-6m','effective_date':'2026-09','summary':'Centralised health-technology assessment begins for new oncology and advanced therapies.','source':'https://health.ec.europa.eu'},
   {'name':'US drug-pricing negotiation expansion','jurisdiction':'US','window':'6-12m','effective_date':'2027-01','summary':'Additional high-spend therapeutics enter negotiated-price selection.','source':'https://www.cms.gov'}],
 'technology':[
   {'name':'EU AI Act — high-risk system obligations','jurisdiction':'EU','window':'6-12m','effective_date':'2027-02','summary':'High-risk AI providers must complete conformity assessments and maintain technical documentation.','source':'https://artificialintelligenceact.eu'},
   {'name':'EU DMA interoperability requirements','jurisdiction':'EU','window':'3-6m','effective_date':'2026-10','summary':'Designated gatekeepers face expanded data-portability and interoperability duties.','source':'https://digital-markets-act.ec.europa.eu'}],
 'fmcg':[{'name':'EU deforestation-free supply chain rule','jurisdiction':'EU','window':'6-12m','effective_date':'2027-01','summary':'Operators must prove key commodities are deforestation-free.','source':'https://environment.ec.europa.eu'}],
 'media':[{'name':'EU Digital Services Act audit cycle','jurisdiction':'EU','window':'3-6m','effective_date':'2026-10','summary':'Large platforms face the next independent systemic-risk audit.','source':'https://digital-strategy.ec.europa.eu'}],
 'retail':[{'name':'EU supply-chain due-diligence duty','jurisdiction':'EU','window':'6-12m','effective_date':'2027-01','summary':'Larger retailers must identify and address adverse labour and environmental impacts.','source':'https://commission.europa.eu'}],
 'professional_services':[{'name':'UK audit-market reform measures','jurisdiction':'UK','window':'6-12m','effective_date':'2027-03','summary':'Operational separation and resilience requirements for major audit firms.','source':'https://www.frc.org.uk'}],
 'travel':[{'name':'EU air passenger rights revision','jurisdiction':'EU','window':'3-6m','effective_date':'2026-10','summary':'Updated compensation thresholds and delay definitions for carriers.','source':'https://transport.ec.europa.eu'}],
}

# ===================== ASSEMBLE =====================
industries = [build_automotive()] + [sample_sector(k) for k in
  ['energy','finance','fmcg','healthcare','media','professional_services','retail','technology','travel']]

def derive_month(base, mb):
    out=[]
    for i in base:
        ps=clamp(round(i['risk_score'] - i['delta']*mb), 8, 99)
        ratio=ps/i['risk_score'] if i['risk_score'] else 1
        out.append({**i,'risk_score':ps,'band':band(ps),
          'delta':round(i['delta']*0.7) or (1 if i['delta']>0 else -1 if i['delta']<0 else 0),
          'sentiment_neg':max(0.14,round(i['sentiment_neg']*ratio,2)),
          'volume_total':round(i['volume_total']*ratio),
          'categories':[{**c,'score':clamp(round(c['score']*ratio),5,99),'volume':round(c['volume']*ratio),'band':band(clamp(round(c['score']*ratio),5,99))} for c in i['categories']],
          'trend':{'weeks':i['trend']['weeks'],'values':[round(v*ratio) for v in i['trend']['values']]},
          'events':i['events']})
    return out

months = {
 '2026-06':{'label':'June 2026','live_sector':'automotive','industries':industries,'regulatory':REG},
 '2026-05':{'label':'May 2026','live_sector':'automotive','industries':derive_month(industries,1),'regulatory':REG},
 '2026-04':{'label':'April 2026','live_sector':'automotive','industries':derive_month(industries,2),'regulatory':REG},
}
out = {
 'schema_version':'2.0','methodology_version':'2.0','data_mode':'prototype',
 'data_mode_note':'PROTOTYPE: Automotive uses real Signal data (2026-06-09) across all 8 themes; volumes/trends real, per-theme negativity & event severity estimated. Other 9 sectors are sample (seed:true). Regulatory items illustrative. Live pipeline replaces all. See pipeline/runbook.md.',
 'generated_at':datetime.datetime.utcnow().isoformat()+'Z',
 'current_month':'2026-06','categories_meta':[{'key':k,'label':l} for k,l in CATS],
 'months':months,
}

here=os.path.dirname(os.path.abspath(__file__))
pub=os.path.join(here,'..','public')
os.makedirs(pub,exist_ok=True)
with open(os.path.join(pub,'data.json'),'w') as f: json.dump(out,f,indent=2)
with open(os.path.join(pub,'data.js'),'w') as f:
    f.write('window.__RISK_DATA__ = '); json.dump(out,f); f.write(';')
hist=os.path.join(here,'..','data','history'); os.makedirs(hist,exist_ok=True)
with open(os.path.join(hist,'2026-06.json'),'w') as f:
    json.dump({'as_of':'2026-06','methodology_version':'2.0',
               'scores':{i['key']:i['risk_score'] for i in industries}},f,indent=2)
print('Wrote public/data.js, public/data.json, data/history/2026-06.json')
for i in industries:
    print(f"  {i['label']:<22} IRS={i['risk_score']:>3} ({i['band']:<8}) seed={i['seed']} vol={i['volume_total']:,}")
