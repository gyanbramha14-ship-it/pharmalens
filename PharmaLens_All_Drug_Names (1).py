import re
from urllib.parse import quote
import pandas as pd
import requests
import streamlit as st

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

st.set_page_config(page_title="PharmaLens", page_icon="💊", layout="wide", initial_sidebar_state="expanded")

st.markdown("""<style>
.stApp{background:#f4f7fb}.block-container{max-width:1450px;padding-top:1.5rem}
.hero{padding:30px;border-radius:24px;color:white;background:linear-gradient(135deg,#075985,#0f766e);box-shadow:0 10px 30px rgba(15,23,42,.18);margin-bottom:18px}
.hero h1{color:white;font-size:2.5rem;margin-bottom:6px}.hero p{color:#e0f2fe;font-size:1.08rem;margin:0}
.notice{background:#fff7ed;color:#7c2d12;border-left:6px solid #f97316;border-radius:12px;padding:14px;margin:12px 0}
.success-box{background:#ecfdf5;color:#064e3b;border-left:6px solid #059669;border-radius:12px;padding:14px;margin:12px 0}
div[data-testid="stMetric"]{background:white;border-radius:15px;padding:12px;box-shadow:0 2px 12px rgba(15,23,42,.08)}
div[data-testid="stExpander"]{border-radius:14px}
</style>""", unsafe_allow_html=True)

# ----------------------------
# API database
# ----------------------------
DRUGS = [{'name': 'Paracetamol',
  'class': 'Analgesic / Antipyretic',
  'forms': ['Tablet', 'Capsule', 'Syrup', 'Suspension', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Pain and fever',
  'solubility': 'Moderately soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture and excessive heat'},
 {'name': 'Ibuprofen',
  'class': 'NSAID',
  'forms': ['Tablet', 'Capsule', 'Suspension', 'Gel'],
  'routes': ['Oral', 'Topical'],
  'uses': 'Pain, inflammation and fever',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Aspirin',
  'class': 'NSAID / Antiplatelet',
  'forms': ['Tablet', 'Chewable Tablet'],
  'routes': ['Oral'],
  'uses': 'Pain, fever and antiplatelet therapy',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Moisture sensitive; hydrolysis may occur'},
 {'name': 'Naproxen',
  'class': 'NSAID',
  'forms': ['Tablet', 'Capsule', 'Suspension'],
  'routes': ['Oral'],
  'uses': 'Pain and inflammation',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Diclofenac',
  'class': 'NSAID',
  'forms': ['Tablet', 'Capsule', 'Gel', 'Injection', 'Suppository'],
  'routes': ['Oral', 'Topical', 'Intramuscular', 'Rectal'],
  'uses': 'Pain and inflammation',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Ketoprofen',
  'class': 'NSAID',
  'forms': ['Capsule', 'Tablet', 'Gel'],
  'routes': ['Oral', 'Topical'],
  'uses': 'Pain and inflammation',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Amoxicillin',
  'class': 'Penicillin Antibiotic',
  'forms': ['Tablet', 'Capsule', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture and excessive heat'},
 {'name': 'Azithromycin',
  'class': 'Macrolide Antibiotic',
  'forms': ['Tablet', 'Capsule', 'Oral Suspension', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Clarithromycin',
  'class': 'Macrolide Antibiotic',
  'forms': ['Tablet', 'Extended-Release Tablet', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Ciprofloxacin',
  'class': 'Fluoroquinolone Antibiotic',
  'forms': ['Tablet', 'Oral Suspension', 'Eye Drops', 'Injection'],
  'routes': ['Oral', 'Ophthalmic', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Levofloxacin',
  'class': 'Fluoroquinolone Antibiotic',
  'forms': ['Tablet', 'Eye Drops', 'Injection'],
  'routes': ['Oral', 'Ophthalmic', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Soluble in acidic conditions',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Moxifloxacin',
  'class': 'Fluoroquinolone Antibiotic',
  'forms': ['Tablet', 'Eye Drops', 'Injection'],
  'routes': ['Oral', 'Ophthalmic', 'Intravenous'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from light'},
 {'name': 'Doxycycline',
  'class': 'Tetracycline Antibiotic',
  'forms': ['Tablet', 'Capsule'],
  'routes': ['Oral'],
  'uses': 'Bacterial infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Metronidazole',
  'class': 'Antibacterial / Antiprotozoal',
  'forms': ['Tablet', 'Suspension', 'Gel', 'Injection'],
  'routes': ['Oral', 'Topical', 'Intravenous'],
  'uses': 'Anaerobic and protozoal infections',
  'solubility': 'Sparingly soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from light'},
 {'name': 'Tinidazole',
  'class': 'Antiprotozoal',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Protozoal and anaerobic infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture'},
 {'name': 'Metoclopramide',
  'class': 'Antiemetic / Gastroprokinetic',
  'forms': ['Tablet', 'Injection', 'Oral Solution'],
  'routes': ['Oral', 'Intravenous', 'Intramuscular'],
  'uses': 'Nausea and vomiting',
  'solubility': 'Soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light'},
 {'name': 'Loperamide',
  'class': 'Antidiarrheal',
  'forms': ['Capsule', 'Tablet', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Diarrhea',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Lactulose',
  'class': 'Osmotic Laxative',
  'forms': ['Oral Solution', 'Syrup'],
  'routes': ['Oral'],
  'uses': 'Constipation and hepatic encephalopathy',
  'solubility': 'Freely soluble in water',
  'dose_type': 'High volume liquid dose',
  'stability': 'Protect from excessive heat'},
 {'name': 'Metformin',
  'class': 'Biguanide Antidiabetic',
  'forms': ['Tablet', 'Extended-Release Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Freely soluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture'},
 {'name': 'Glimepiride',
  'class': 'Sulfonylurea Antidiabetic',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from moisture and light'},
 {'name': 'Gliclazide',
  'class': 'Sulfonylurea Antidiabetic',
  'forms': ['Tablet', 'Modified-Release Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Sitagliptin',
  'class': 'DPP-4 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Vildagliptin',
  'class': 'DPP-4 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Dapagliflozin',
  'class': 'SGLT2 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Diabetes and selected cardiovascular or renal conditions',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Empagliflozin',
  'class': 'SGLT2 Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Diabetes and selected cardiovascular or renal conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Pioglitazone',
  'class': 'Thiazolidinedione',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Type 2 diabetes',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Levothyroxine',
  'class': 'Thyroid Hormone',
  'forms': ['Tablet', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Hypothyroidism',
  'solubility': 'Very slightly soluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Sensitive to light and moisture'},
 {'name': 'Amlodipine',
  'class': 'Calcium Channel Blocker',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Hypertension and angina',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Ketoconazole',
  'class': 'Imidazole Antifungal',
  'forms': ['Cream', 'Shampoo', 'Tablet'],
  'routes': ['Topical', 'Oral'],
  'uses': 'Fungal infections',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light'},
 {'name': 'Fluconazole',
  'class': 'Triazole Antifungal',
  'forms': ['Tablet', 'Capsule', 'Oral Suspension', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Fungal infections',
  'solubility': 'Soluble in water',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Acyclovir',
  'class': 'Antiviral',
  'forms': ['Tablet', 'Cream', 'Ointment', 'Injection'],
  'routes': ['Oral', 'Topical', 'Intravenous'],
  'uses': 'Herpes virus infections',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from moisture'},
 {'name': 'Oseltamivir',
  'class': 'Antiviral',
  'forms': ['Capsule', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Influenza',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Hydrocortisone',
  'class': 'Corticosteroid',
  'forms': ['Cream', 'Ointment', 'Tablet', 'Injection'],
  'routes': ['Topical', 'Oral', 'Intravenous'],
  'uses': 'Inflammatory and allergic conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light'},
 {'name': 'Betamethasone',
  'class': 'Corticosteroid',
  'forms': ['Cream', 'Ointment', 'Tablet', 'Injection'],
  'routes': ['Topical', 'Oral', 'Intramuscular'],
  'uses': 'Inflammatory and allergic conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Adapalene',
  'class': 'Topical Retinoid',
  'forms': ['Gel', 'Cream'],
  'routes': ['Topical'],
  'uses': 'Acne',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Tretinoin',
  'class': 'Topical Retinoid',
  'forms': ['Cream', 'Gel', 'Lotion'],
  'routes': ['Topical'],
  'uses': 'Acne and selected dermatological conditions',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Povidone Iodine',
  'class': 'Antiseptic',
  'forms': ['Solution', 'Ointment', 'Gargle'],
  'routes': ['Topical', 'Oral cavity'],
  'uses': 'Antisepsis',
  'solubility': 'Soluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Chlorhexidine',
  'class': 'Antiseptic',
  'forms': ['Solution', 'Gel', 'Mouthwash'],
  'routes': ['Topical', 'Oral cavity'],
  'uses': 'Antisepsis and oral hygiene',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Silver Sulfadiazine',
  'class': 'Topical Antimicrobial',
  'forms': ['Cream'],
  'routes': ['Topical'],
  'uses': 'Burn wound infection prevention',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from light'},
 {'name': 'Calamine',
  'class': 'Topical Protective',
  'forms': ['Lotion', 'Cream'],
  'routes': ['Topical'],
  'uses': 'Skin irritation and itching',
  'solubility': 'Insoluble in water',
  'dose_type': 'Topical',
  'stability': 'Protect from contamination'},
 {'name': 'Lidocaine',
  'class': 'Local Anesthetic',
  'forms': ['Gel', 'Cream', 'Injection', 'Spray'],
  'routes': ['Topical', 'Local', 'Intravenous'],
  'uses': 'Local anesthesia',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from light'},
 {'name': 'Bupivacaine',
  'class': 'Local Anesthetic',
  'forms': ['Injection'],
  'routes': ['Local', 'Epidural'],
  'uses': 'Local and regional anesthesia',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Low dose',
  'stability': 'Sterile product; protect from light'},
 {'name': 'Tramadol',
  'class': 'Opioid Analgesic',
  'forms': ['Tablet', 'Capsule', 'Oral Drops', 'Injection'],
  'routes': ['Oral', 'Intravenous', 'Intramuscular'],
  'uses': 'Moderate pain',
  'solubility': 'Soluble depending on salt form',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Gabapentin',
  'class': 'Anticonvulsant / Neuropathic Pain Agent',
  'forms': ['Capsule', 'Tablet', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Neuropathic pain and seizure disorders',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from moisture'},
 {'name': 'Pregabalin',
  'class': 'Anticonvulsant / Neuropathic Pain Agent',
  'forms': ['Capsule', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Neuropathic pain and seizure disorders',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Ferrous Sulfate',
  'class': 'Hematinic',
  'forms': ['Tablet', 'Capsule', 'Syrup'],
  'routes': ['Oral'],
  'uses': 'Iron deficiency',
  'solubility': 'Soluble depending on hydrate and medium',
  'dose_type': 'Medium dose',
  'stability': 'Protect from moisture and oxidation'},
 {'name': 'Folic Acid',
  'class': 'Vitamin',
  'forms': ['Tablet', 'Oral Solution'],
  'routes': ['Oral'],
  'uses': 'Folate deficiency',
  'solubility': 'Slightly soluble in water',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Calcium Carbonate',
  'class': 'Mineral Supplement / Antacid',
  'forms': ['Tablet', 'Chewable Tablet', 'Suspension'],
  'routes': ['Oral'],
  'uses': 'Calcium supplementation and antacid use',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'High dose',
  'stability': 'Protect from moisture'},
 {'name': 'Vitamin D3',
  'class': 'Vitamin',
  'forms': ['Tablet', 'Capsule', 'Oral Drops'],
  'routes': ['Oral'],
  'uses': 'Vitamin D supplementation',
  'solubility': 'Fat soluble',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light and oxidation'},
 {'name': 'Vitamin B12',
  'class': 'Vitamin',
  'forms': ['Tablet', 'Injection', 'Oral Solution'],
  'routes': ['Oral', 'Intramuscular'],
  'uses': 'Vitamin B12 supplementation',
  'solubility': 'Soluble depending on form',
  'dose_type': 'Very low dose',
  'stability': 'Protect from light'},
 {'name': 'Zinc Sulfate',
  'class': 'Mineral Supplement',
  'forms': ['Tablet', 'Capsule', 'Syrup'],
  'routes': ['Oral'],
  'uses': 'Zinc supplementation',
  'solubility': 'Soluble in water',
  'dose_type': 'Low to medium dose',
  'stability': 'Protect from moisture'},
 {'name': 'Potassium Chloride',
  'class': 'Electrolyte',
  'forms': ['Extended-Release Tablet', 'Oral Solution', 'Injection'],
  'routes': ['Oral', 'Intravenous'],
  'uses': 'Potassium replacement',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from moisture'},
 {'name': 'Sodium Chloride',
  'class': 'Electrolyte',
  'forms': ['Injection', 'Nasal Solution', 'Tablet'],
  'routes': ['Intravenous', 'Nasal', 'Oral'],
  'uses': 'Electrolyte replacement and irrigation',
  'solubility': 'Freely soluble in water',
  'dose_type': 'Medium to high dose',
  'stability': 'Protect from contamination'},
 {'name': 'Insulin Human',
  'class': 'Antidiabetic Hormone',
  'forms': ['Injection', 'Cartridge'],
  'routes': ['Subcutaneous', 'Intravenous'],
  'uses': 'Diabetes',
  'solubility': 'Protein formulation',
  'dose_type': 'Biologic dose',
  'stability': 'Temperature controlled; avoid freezing'},
 {'name': 'Sildenafil',
  'class': 'PDE-5 Inhibitor',
  'forms': ['Tablet', 'Oral Suspension'],
  'routes': ['Oral'],
  'uses': 'Selected cardiovascular and sexual health indications',
  'solubility': 'Slightly soluble depending on salt form',
  'dose_type': 'Low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Tamsulosin',
  'class': 'Alpha-1 Adrenergic Blocker',
  'forms': ['Modified-Release Capsule'],
  'routes': ['Oral'],
  'uses': 'Lower urinary tract symptoms',
  'solubility': 'Slightly soluble depending on salt form',
  'dose_type': 'Very low dose',
  'stability': 'Protect from moisture'},
 {'name': 'Finasteride',
  'class': '5-Alpha Reductase Inhibitor',
  'forms': ['Tablet'],
  'routes': ['Oral'],
  'uses': 'Selected prostate and hair-loss indications',
  'solubility': 'Practically insoluble in water',
  'dose_type': 'Low dose',
  'stability': 'Protect from light and moisture'}]

EXCIPIENTS = {'Diluent': ['Microcrystalline cellulose',
             'Lactose monohydrate',
             'Dicalcium phosphate',
             'Mannitol',
             'Calcium carbonate'],
 'Binder': ['Povidone', 'Pregelatinized starch', 'Hydroxypropyl cellulose', 'Hypromellose'],
 'Disintegrant': ['Croscarmellose sodium', 'Crospovidone', 'Sodium starch glycolate'],
 'Lubricant': ['Magnesium stearate', 'Stearic acid', 'Sodium stearyl fumarate'],
 'Glidant': ['Colloidal silicon dioxide', 'Talc'],
 'Suspending agent': ['Sodium carboxymethylcellulose', 'Xanthan gum', 'Methylcellulose'],
 'Preservative': ['Methylparaben', 'Propylparaben', 'Potassium sorbate', 'Sodium benzoate'],
 'Vehicle': ['Purified water', 'Glycerin', 'Propylene glycol', 'Polyethylene glycol'],
 'Sweetener': ['Sucrose', 'Sorbitol', 'Sucralose', 'Saccharin sodium'],
 'Film former': ['Hypromellose', 'Polyvinyl alcohol', 'Cellulose derivatives'],
 'Topical base': ['White soft paraffin', 'Liquid paraffin', 'Carbomer', 'Cetostearyl alcohol'],
 'Sterile vehicle': ['Water for Injection', 'Sodium chloride solution', 'Phosphate buffer']}

PROCESS_DATA = {'Tablet': {'process': ['Dispensing and material verification',
                        'Sifting or milling where justified',
                        'Blending or granulation',
                        'Drying and moisture control where applicable',
                        'Final blending and lubrication',
                        'Compression',
                        'Optional film coating',
                        'Packing and reconciliation'],
            'defects': ['Weight variation from poor powder flow',
                        'Capping or lamination from air entrapment or compression conditions',
                        'Sticking or picking from excess moisture or tooling issues',
                        'Chipping from weak granules or insufficient binding',
                        'Slow dissolution from over-lubrication or excessive hardness',
                        'Content-uniformity failure from segregation'],
            'tests': ['Appearance',
                      'Weight variation',
                      'Hardness',
                      'Friability',
                      'Disintegration',
                      'Dissolution',
                      'Assay',
                      'Content uniformity']},
 'Capsule': {'process': ['Dispensing and sieving',
                         'Powder blending or granulation',
                         'Flow and bulk-density evaluation',
                         'Capsule filling',
                         'Fill-weight checks',
                         'Visual inspection',
                         'Packing and reconciliation'],
             'defects': ['Fill-weight variation',
                         'Poor flow and machine blockage',
                         'Capsule body-cap separation',
                         'Powder leakage',
                         'Content-uniformity failure',
                         'Moisture-related brittleness or softening'],
             'tests': ['Appearance',
                       'Fill-weight variation',
                       'Disintegration',
                       'Dissolution',
                       'Assay',
                       'Content uniformity',
                       'Moisture']},
 'Liquid': {'process': ['Vehicle preparation',
                        'Dissolution or dispersion of ingredients',
                        'pH adjustment where required',
                        'Addition of sweetener, flavor and preservative',
                        'Volume make-up',
                        'Filtration or homogenization where justified',
                        'Filling and packing'],
            'defects': ['Precipitation or crystallization',
                        'Incorrect pH',
                        'Microbial contamination',
                        'Viscosity variation',
                        'Sedimentation',
                        'Fill-volume variation',
                        'Color or flavor instability'],
            'tests': ['Appearance',
                      'pH',
                      'Viscosity',
                      'Specific gravity',
                      'Assay',
                      'Microbial limits',
                      'Fill volume',
                      'Stability']},
 'Suspension': {'process': ['Vehicle preparation',
                            'Wetting and dispersion of API',
                            'Particle-size control',
                            'Addition of suspending agents',
                            'Homogenization',
                            'pH and viscosity adjustment',
                            'Filling and packing'],
                'defects': ['Rapid sedimentation',
                            'Caking and poor redispersibility',
                            'Particle-size growth',
                            'Viscosity drift',
                            'Foaming',
                            'Microbial contamination',
                            'Dose non-uniformity'],
                'tests': ['Appearance',
                          'pH',
                          'Viscosity',
                          'Particle-size distribution',
                          'Sedimentation volume',
                          'Redispersibility',
                          'Assay',
                          'Microbial limits']},
 'Sterile': {'process': ['Raw-material and container verification',
                         'Solution or suspension preparation',
                         'pH and osmolality adjustment',
                         'Sterile filtration where applicable',
                         'Aseptic filling or validated terminal sterilization',
                         'Container closure',
                         'Visual inspection',
                         'Packaging and quarantine release'],
             'defects': ['Sterility failure',
                         'Bacterial endotoxin failure',
                         'Particulate contamination',
                         'pH or osmolality variation',
                         'Fill-volume variation',
                         'Container-closure leakage',
                         'Precipitation or loss of potency'],
             'tests': ['Appearance',
                       'pH',
                       'Assay',
                       'Sterility',
                       'Bacterial endotoxins',
                       'Particulate matter',
                       'Fill volume',
                       'Container-closure integrity']},
 'Topical': {'process': ['Oil-phase or base preparation',
                         'Aqueous-phase preparation where applicable',
                         'API levigation, dissolution or dispersion',
                         'Emulsification or polymer hydration',
                         'Homogenization',
                         'Cooling and de-aeration',
                         'Filling and packing'],
             'defects': ['Phase separation',
                         'Creaming or cracking',
                         'Lumping or grittiness',
                         'Viscosity variation',
                         'Air entrapment',
                         'Microbial contamination',
                         'Non-uniform API distribution'],
             'tests': ['Appearance',
                       'Homogeneity',
                       'pH',
                       'Viscosity',
                       'Spreadability',
                       'Assay',
                       'Microbial limits',
                       'Stability']}}

# ----------------------------
# Generic-product metadata
# ----------------------------
GENERIC_STATUS = {'Paracetamol': ('Generic products widely available',
                 'Small-molecule generic',
                 'Reference/brand status is country-specific.'),
 'Ibuprofen': ('Generic products widely available',
               'Small-molecule generic',
               'Reference/brand status is country-specific.'),
 'Aspirin': ('Generic products widely available',
             'Small-molecule generic',
             'Reference/brand status is country-specific.'),
 'Naproxen': ('Generic products widely available',
              'Small-molecule generic',
              'Reference/brand status is country-specific.'),
 'Diclofenac': ('Generic products widely available',
                'Small-molecule generic',
                'Reference/brand status is country-specific.'),
 'Amoxicillin': ('Generic products widely available',
                 'Small-molecule generic',
                 'Check salt/strength/dosage form.'),
 'Azithromycin': ('Generic products widely available',
                  'Small-molecule generic',
                  'Check salt/strength/dosage form.'),
 'Metformin': ('Generic products widely available',
               'Small-molecule generic',
               'Immediate-release and extended-release are different products.'),
 'Amlodipine': ('Generic products widely available',
                'Small-molecule generic',
                'Salt form/strength should be verified.'),
 'Fluconazole': ('Generic products widely available',
                 'Small-molecule generic',
                 'Check dosage form and strength.'),
 'Insulin Human': ('Biosimilar/biological-product pathway; not conventional small-molecule generic',
                   'Biologic',
                   'Interchangeability/biosimilarity is jurisdiction-specific.')}

STUDY_DATA = {'Paracetamol': {'in_vitro': [['Dissolution',
                               'Dissolution medium, pH, apparatus, rpm, sampling times, % drug released'],
                              ['Assay / content',
                               'Assay %, content uniformity, analytical method, calibration range'],
                              ['Drug-excipient compatibility',
                               'FTIR/DSC/TGA, physical appearance, degradation markers'],
                              ['Stability',
                               'Assay, degradation products, dissolution, moisture, appearance']],
                 'in_vivo': [['Pharmacokinetics',
                              'Cmax, Tmax, AUC, t1/2, kel, relative/absolute bioavailability'],
                             ['Bioequivalence', 'Test/reference AUC and Cmax, geometric mean ratio, 90% CI'],
                             ['Efficacy / pharmacodynamics',
                              'Pain/fever endpoint as applicable to study design'],
                             ['Safety', 'Adverse events, clinical observations, laboratory parameters']]},
 'Ibuprofen': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, time points, % released'],
                            ['Solubility', 'Equilibrium solubility versus pH, temperature, salt/form'],
                            ['Permeability', 'Apparent permeability / transport direction where applicable'],
                            ['Compatibility', 'DSC/FTIR and degradation/interaction assessment']],
               'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2, clearance, volume of distribution'],
                           ['Bioequivalence', 'AUC and Cmax test/reference comparison with 90% CI'],
                           ['Pharmacodynamics', 'Pain/inflammation endpoints where studied'],
                           ['Safety', 'GI and other adverse events, clinical/lab observations']]},
 'Metformin': {'in_vitro': [['Dissolution', 'Multiple pH media, apparatus, rpm, sampling times, % release'],
                            ['Release kinetics',
                             'Zero-order/first-order/Higuchi/Korsmeyer-Peppas fitting where justified'],
                            ['Assay / content uniformity',
                             'Assay %, individual content, acceptance criteria'],
                            ['Compatibility', 'FTIR/DSC and moisture/stability assessment']],
               'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2, renal elimination-related parameters'],
                           ['Bioequivalence', 'AUC and Cmax comparison of test/reference products'],
                           ['Food effect',
                            'AUC/Cmax and Tmax under fed versus fasted conditions where studied'],
                           ['Safety', 'Adverse events and clinical/laboratory observations']]},
 'Amlodipine': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, sampling times, % release'],
                             ['Assay', 'Potency, content uniformity, related substances'],
                             ['Compatibility', 'DSC/FTIR and degradation assessment'],
                             ['Stability',
                              'Assay, impurities, dissolution, appearance under storage conditions']],
                'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2'],
                            ['Bioequivalence', 'AUC/Cmax test-reference ratio and 90% CI'],
                            ['Food effect', 'PK parameters under fed/fasted conditions where studied'],
                            ['Safety', 'Adverse events and clinical/laboratory parameters']]},
 'Amoxicillin': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, time points, % release'],
                              ['Assay', 'Potency, content uniformity, related substances'],
                              ['Stability', 'Assay, degradation products, moisture and dissolution'],
                              ['Antibacterial activity',
                               'MIC/MBC or zone of inhibition when formulation/product study includes '
                               'microbiology']],
                 'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2'],
                             ['Bioequivalence', 'AUC/Cmax test-reference comparison'],
                             ['Antibacterial efficacy',
                              'Microbiological/clinical endpoint according to study design'],
                             ['Safety', 'Adverse events and laboratory parameters']]},
 'Diclofenac': {'in_vitro': [['Dissolution / release',
                              'Medium, pH, apparatus, rpm, sampling times, % release'],
                             ['Topical permeation',
                              'Flux, permeability coefficient, cumulative amount permeated, skin retention'],
                             ['Assay / impurities', 'Assay, related substances, content uniformity'],
                             ['Stability', 'Assay, impurities, dissolution/release, appearance']],
                'in_vivo': [['PK', 'Cmax, Tmax, AUC, t1/2'],
                            ['Bioequivalence', 'AUC/Cmax comparison where applicable'],
                            ['Pharmacodynamic efficacy',
                             'Pain/inflammation outcome measures according to design'],
                            ['Safety', 'Adverse events and clinical/lab parameters']]},
 'Aspirin': {'in_vitro': [['Dissolution', 'Medium/pH, apparatus, rpm, sampling times, % release'],
                          ['Hydrolysis / stability',
                           'Aspirin degradation, salicylic acid formation, moisture'],
                          ['Assay', 'Potency, related substances, content uniformity'],
                          ['Compatibility', 'DSC/FTIR and excipient interaction assessment']],
             'in_vivo': [['PK', 'Salicylate/acetylsalicylic acid-related Cmax, Tmax, AUC where measured'],
                         ['Pharmacodynamic platelet effect',
                          'Platelet aggregation or thromboxane-related endpoint where studied'],
                         ['Bioequivalence', 'PK/PD comparison according to product and regulatory design'],
                         ['Safety', 'Bleeding/GI and other adverse events as appropriate']]}}


def find_drug(name):
    return next((item for item in DRUGS if item["name"] == name), None)

def clean_text(value):
    if isinstance(value,list): return " ".join(str(x) for x in value)
    return str(value) if value else "Not available"

def get_process_type(form):
    tablet=["Tablet","Delayed-Release Tablet","Chewable Tablet","Extended-Release Tablet","Modified-Release Tablet","Orally Disintegrating Tablet","Sublingual Tablet","Vaginal Tablet","Granules","Lozenge"]
    capsule=["Capsule","Delayed-Release Capsule","Modified-Release Capsule"]
    liquid=["Syrup","Oral Solution","Oral Drops","Nasal Solution","Solution","Mouthwash","Gargle"]
    suspension=["Suspension","Oral Suspension","Nebulizer Suspension"]
    sterile=["Injection","Eye Drops"]
    topical=["Cream","Gel","Ointment","Lotion","Shampoo"]
    if form in tablet:return "Tablet"
    if form in capsule:return "Capsule"
    if form in liquid:return "Liquid"
    if form in suspension:return "Suspension"
    if form in sterile:return "Sterile"
    if form in topical:return "Topical"
    return "Tablet"

def get_daily_med_search_url(name):
    return "https://dailymed.nlm.nih.gov/dailymed/search.cfm?query="+quote(name)

def get_pubmed_search_url(name, study_type=None):
    query=f'"{name}"'
    if study_type=="In vitro": query+=' AND (in vitro OR dissolution OR permeability OR "drug release")'
    if study_type=="In vivo": query+=' AND (in vivo OR pharmacokinetic OR bioavailability OR bioequivalence)'
    return "https://pubmed.ncbi.nlm.nih.gov/?term="+quote(query)

def get_suggestions(drug,form):
    result={}
    tablet=["Tablet","Delayed-Release Tablet","Chewable Tablet","Extended-Release Tablet","Modified-Release Tablet","Orally Disintegrating Tablet","Sublingual Tablet","Vaginal Tablet"]
    capsule=["Capsule","Delayed-Release Capsule","Modified-Release Capsule"]
    liquid=["Syrup","Oral Solution","Suspension","Oral Suspension","Oral Drops","Nasal Solution","Solution","Mouthwash","Gargle"]
    topical=["Cream","Gel","Ointment","Lotion","Shampoo"]; sterile=["Injection","Eye Drops"]
    if form in tablet:
        result["Diluent"]=EXCIPIENTS["Diluent"]; result["Binder"]=EXCIPIENTS["Binder"]; result["Disintegrant"]=EXCIPIENTS["Disintegrant"]; result["Lubricant"]=EXCIPIENTS["Lubricant"]; result["Glidant"]=EXCIPIENTS["Glidant"]
    if form in capsule:
        result["Capsule-fill diluent"]=EXCIPIENTS["Diluent"]; result["Binder or granulation aid"]=EXCIPIENTS["Binder"]; result["Glidant"]=EXCIPIENTS["Glidant"]; result["Lubricant"]=EXCIPIENTS["Lubricant"]
    if form in liquid:
        result["Vehicle"]=EXCIPIENTS["Vehicle"]; result["Preservative"]=EXCIPIENTS["Preservative"]; result["Sweetener"]=EXCIPIENTS["Sweetener"]
    if form in ["Suspension","Oral Suspension"]: result["Suspending agent"]=EXCIPIENTS["Suspending agent"]
    if form in topical: result["Topical base"]=EXCIPIENTS["Topical base"]; result["Preservative"]=EXCIPIENTS["Preservative"]
    if form in sterile: result["Sterile vehicle"]=EXCIPIENTS["Sterile vehicle"]
    if "Practically insoluble" in drug["solubility"]:
        result["Solubility-development topics"]=["Particle-size reduction","Surfactant screening","Cosolvent screening","Salt or pH screening","Solid-dispersion investigation"]
    if "Very low dose" in drug["dose_type"]:
        result["Low-dose control topics"]=["Content uniformity","Geometric dilution","Blend segregation study","Validated assay method"]
    if "High dose" in drug["dose_type"]:
        result["High-dose control topics"]=["Drug-loading capability","Blend uniformity","Powder flow","Dosage-form size"]
    return result

@st.cache_data(ttl=86400,show_spinner=False)
def get_pubchem_data(name):
    props="IUPACName,MolecularFormula,MolecularWeight,CanonicalSMILES,IsomericSMILES,HBondDonorCount,HBondAcceptorCount,RotatableBondCount,XLogP,TPSA"
    url="https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/"+quote(name)+"/property/"+props+"/JSON"
    try:
        r=requests.get(url,timeout=25)
        if r.status_code!=200:return {"Status":"No PubChem record found"}
        x=r.json()["PropertyTable"]["Properties"][0]
        return {"PubChem CID":x.get("CID","Not available"),"IUPAC Name":x.get("IUPACName","Not available"),"Molecular Formula":x.get("MolecularFormula","Not available"),"Molecular Weight":x.get("MolecularWeight","Not available"),"Hydrogen Bond Donors":x.get("HBondDonorCount","Not available"),"Hydrogen Bond Acceptors":x.get("HBondAcceptorCount","Not available"),"Rotatable Bonds":x.get("RotatableBondCount","Not available"),"XLogP":x.get("XLogP","Not available"),"TPSA":x.get("TPSA","Not available"),"Canonical SMILES":x.get("ConnectivitySMILES","Not available"),"Isomeric SMILES":x.get("SMILES","Not available")}
    except Exception as e:return {"Error":str(e)}

@st.cache_data(ttl=86400,show_spinner=False)
def get_openfda_data(name):
    url="https://api.fda.gov/drug/label.json?search=openfda.generic_name:"+quote(name.lower())+"&limit=1"
    try:
        r=requests.get(url,timeout=25)
        if r.status_code!=200:return {"Status":"No matching openFDA label found"}
        x=r.json()["results"][0]; o=x.get("openfda",{})
        return {"Indications":clean_text(x.get("indications_and_usage")),"Warnings":clean_text(x.get("warnings")),"Dosage and Administration":clean_text(x.get("dosage_and_administration")),"Routes":clean_text(x.get("route")),"Manufacturers":clean_text(x.get("manufacturer_name")),"OpenFDA Brand Names":clean_text(o.get("brand_name")),"OpenFDA Generic Names":clean_text(o.get("generic_name")),"Product Type":clean_text(o.get("product_type"))}
    except Exception as e:return {"Error":str(e)}

@st.cache_data(ttl=86400,show_spinner=False)
def get_dailymed_records(name):
    url="https://dailymed.nlm.nih.gov/dailymed/services/v2/spls.json?drug_name="+quote(name)
    try:
        r=requests.get(url,timeout=30)
        if r.status_code!=200:return []
        d=r.json()
        if isinstance(d,list):return d
        if isinstance(d,dict):
            for k in ["data","results","spls"]:
                if isinstance(d.get(k),list):return d[k]
        return []
    except Exception:return []

def normalize_dailymed_records(records):
    rows=[]
    for x in records[:30]:
        sid=x.get("setid") or x.get("setId") or x.get("set_id") or x.get("SETID") or ""
        title=x.get("title") or x.get("drug_name") or x.get("drugName") or x.get("name") or "DailyMed label"
        manufacturer=x.get("labeler") or x.get("manufacturer") or x.get("companyName") or "Not listed"
        url="https://dailymed.nlm.nih.gov/dailymed/drugInfo.cfm?setid="+quote(str(sid)) if sid else ""
        rows.append({"Product / label":title,"Manufacturer":manufacturer,"Set ID":sid or "Not available","Label URL":url})
    return rows

@st.cache_data(ttl=86400,show_spinner=False)
def get_dailymed_xml(set_id):
    try:
        r=requests.get("https://dailymed.nlm.nih.gov/dailymed/services/v2/spls/"+quote(str(set_id))+".xml",timeout=35)
        return r.text if r.status_code==200 else ""
    except Exception:return ""

def extract_inactive_ingredients(xml_text):
    if not xml_text or BeautifulSoup is None:return []
    soup=BeautifulSoup(xml_text,"xml"); out=[]
    for e in soup.find_all(string=re.compile("inactive ingredients",re.I)):
        for node in e.parent.find_all_next(["ingredient","ingredientSubstance"],limit=100):
            t=node.get_text(" ",strip=True)
            if t and t not in out:out.append(t)
        if out:break
    return out[:100]

st.markdown("""<div class="hero"><h1>💊 PharmaLens 100</h1><p>API properties, dosage forms, product-label ingredients, formulation development, manufacturing risk and research-study intelligence.</p></div>""",unsafe_allow_html=True)
st.markdown("""<div class="notice"><b>Educational-use notice:</b> Study parameters are a research framework, not actual study results. Verify original publications, protocols and regulatory guidance before using them in academic or regulatory work.</div>""",unsafe_allow_html=True)

st.sidebar.header("🔎 API search")
search_text=st.sidebar.text_input("Search API",placeholder="Example: Paracetamol")
filtered=[d for d in DRUGS if search_text.lower() in d["name"].lower()] if search_text else DRUGS
if not filtered:st.error("API not found. Try another spelling.");st.stop()
selected_name=st.sidebar.selectbox("Select API",[d["name"] for d in filtered])
selected_drug=find_drug(selected_name)
selected_form=st.sidebar.selectbox("Select dosage form",selected_drug["forms"])
st.sidebar.divider();st.sidebar.metric("APIs loaded",len(DRUGS))

m1,m2,m3,m4=st.columns(4)
with m1:st.metric("API",selected_drug["name"])
with m2:st.metric("Class",selected_drug["class"])
with m3:st.metric("Market forms",len(selected_drug["forms"]))
with m4:st.metric("Selected form",selected_form)

tabs=st.tabs(["🧬 API profile","🌐 Live properties","🧪 Exact ingredients","🔬 In-vitro / In-vivo","🏭 Process defects","📋 Development notes"])

with tabs[0]:
    st.subheader("API profile")
    profile=pd.DataFrame([["API name",selected_drug["name"]],["Therapeutic class",selected_drug["class"]],["Common use",selected_drug["uses"]],["Solubility note",selected_drug["solubility"]],["Dose category",selected_drug["dose_type"]],["Stability note",selected_drug["stability"]],["Marketed dosage forms",", ".join(selected_drug["forms"])],["Routes",", ".join(selected_drug["routes"])]],columns=["Property","Information"])
    st.dataframe(profile,use_container_width=True,hide_index=True)
    st.subheader("💊 Generic / product-status intelligence")
    status,ptype,note=GENERIC_STATUS.get(selected_name,("Not curated in local database","Needs verification","Generic status is product-, strength-, dosage-form- and jurisdiction-specific."))
    st.dataframe(pd.DataFrame([["Generic product availability",status],["Product type",ptype],["Interpretation",note],["Important distinction","API = active ingredient; generic = medicinal product using the API and meeting applicable regulatory requirements."]],columns=["Field","Information"]),use_container_width=True,hide_index=True)
    st.info("A generic/brand decision is jurisdiction-specific. For regulatory work, verify the exact product, reference product, strength, dosage form and applicable bioequivalence requirements.")

with tabs[1]:
    st.subheader("Live public properties")
    if st.button("Fetch PubChem + openFDA data",type="primary",use_container_width=True):
        with st.spinner("Fetching public data..."):
            pc=get_pubchem_data(selected_name);fd=get_openfda_data(selected_name)
        st.write("### PubChem chemical properties");st.json(pc)
        st.write("### openFDA label information")
        if "Error" in fd or "Status" in fd:st.warning(fd)
        else:
            for title,value in fd.items():
                with st.expander(title):st.write(value)

with tabs[2]:
    st.subheader(f"Product-specific ingredients: {selected_name}")
    st.markdown("""<div class="success-box">Exact inactive ingredients depend on product, strength, manufacturer, country and dosage form. Select a specific DailyMed label before treating an ingredient list as product-specific.</div>""",unsafe_allow_html=True)
    st.link_button("🔗 Open DailyMed manual search",get_daily_med_search_url(selected_name),use_container_width=True)
    if st.button("Search current DailyMed records",use_container_width=True):
        rec=normalize_dailymed_records(get_dailymed_records(selected_name))
        if rec:
            st.dataframe(pd.DataFrame(rec),use_container_width=True,hide_index=True)
            ids=[x["Set ID"] for x in rec if x["Set ID"]!="Not available"]
            if ids:
                sid=st.selectbox("Select a product Set ID",ids)
                if st.button("Read inactive ingredients from selected label"):
                    ing=extract_inactive_ingredients(get_dailymed_xml(sid))
                    if ing:st.dataframe(pd.DataFrame({"Product-specific ingredient record":ing}),use_container_width=True,hide_index=True)
                    else:st.warning("Automatic extraction failed. Open the original DailyMed label manually.")
        else:st.warning("No DailyMed API records were returned.")
    st.subheader("Role-based excipient development suggestions")
    rows=[{"Role / development topic":r,"Examples":", ".join(v),"Development note":"Confirm grade, compatibility, concentration, safety, regulatory status and stability."} for r,v in get_suggestions(selected_drug,selected_form).items()]
    if rows:st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
    st.link_button("🔗 FDA Inactive Ingredient Database","https://www.accessdata.fda.gov/scripts/cder/iig/index.cfm",use_container_width=True)

with tabs[3]:
    st.subheader(f"🔬 Research studies: {selected_name}")
    st.markdown("""<div class="notice"><b>In-vitro:</b> outside a living organism. <b>In-vivo:</b> in a living organism. The tables below show study types and parameters to look for. They are not claimed study results.</div>""",unsafe_allow_html=True)
    c1,c2=st.columns(2)
    with c1:st.link_button("🔎 PubMed: In-vitro studies",get_pubmed_search_url(selected_name,"In vitro"),use_container_width=True)
    with c2:st.link_button("🔎 PubMed: In-vivo / PK / BE studies",get_pubmed_search_url(selected_name,"In vivo"),use_container_width=True)
    study=STUDY_DATA.get(selected_name)
    if study:
        st.write("### 🧪 In-vitro study parameters")
        st.dataframe(pd.DataFrame(study["in_vitro"],columns=["Study / endpoint","Important parameters"]),use_container_width=True,hide_index=True)
        st.write("### 🐀 In-vivo study parameters")
        st.dataframe(pd.DataFrame(study["in_vivo"],columns=["Study / endpoint","Important parameters"]),use_container_width=True,hide_index=True)
    else:st.warning("No curated API-specific framework is stored locally for this API yet. Use the PubMed search links for the actual literature.")
    st.write("### 📌 Parameter glossary")
    st.dataframe(pd.DataFrame([["Cmax","Maximum observed plasma concentration"],["Tmax","Time to reach Cmax"],["AUC","Systemic exposure over a defined interval"],["t1/2","Time for concentration to decrease by half during the relevant elimination phase"],["Bioavailability","Extent/rate of drug reaching systemic circulation, depending on route and definition"],["Bioequivalence","Comparison of relevant exposure between test and reference products under the applicable regulatory criteria"],["Dissolution","Rate and extent at which drug goes into solution from the dosage form"],["Permeability","Ability to cross a biological membrane/model barrier"],["MIC","Minimum inhibitory concentration"]],columns=["Parameter","Simple meaning"]),use_container_width=True,hide_index=True)

with tabs[4]:
    process=PROCESS_DATA[get_process_type(selected_form)]
    st.subheader(f"High-level manufacturing risk map: {selected_form}")
    st.write("### Process stages")
    for n,step in enumerate(process["process"],1):st.write(f"{n}. {step}")
    st.write("### Possible defects")
    st.dataframe(pd.DataFrame([{"Possible defect":d,"Investigation focus":"Review material attributes, equipment status, process parameters, IPC data, deviation history, cleaning and batch documentation."} for d in process["defects"]]),use_container_width=True,hide_index=True)
    st.write("### Typical quality checks")
    st.dataframe(pd.DataFrame({"Quality check":process["tests"],"Purpose":["Confirm dosage-form performance and consistency"]*len(process["tests"])}),use_container_width=True,hide_index=True)
    st.warning("Actual production must follow approved specifications, validated processes, GMP requirements, authorized SOPs and approved batch records.")

with tabs[5]:
    st.subheader("Formulation-development checklist")
    for item in ["Confirm API identity, assay, polymorph or salt form where relevant","Evaluate particle size, flow, density, moisture and compatibility","Select dosage form based on therapeutic need and product performance","Screen excipient compatibility and concentration ranges","Define critical quality attributes","Identify critical material attributes and process parameters","Perform stability and packaging studies","Define in-process controls and acceptance criteria","Investigate defects through documented root-cause analysis","Use CAPA and continued process verification after validation"]:
        st.checkbox(item,value=False)

st.divider()
st.caption("PharmaLens 100 | Educational research dashboard | Always verify current product labels, publications and regulatory requirements.")
