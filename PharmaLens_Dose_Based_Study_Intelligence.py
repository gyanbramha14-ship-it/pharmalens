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


# ----------------------------
# Research-intelligence engine
# ----------------------------

def _first_text(value):
    if isinstance(value, list):
        return " ".join(str(x) for x in value)
    return str(value or "")


def _pubmed_url(pmid):
    return f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"


def _doi_url(doi):
    return f"https://doi.org/{doi}" if doi else ""


def _strip_xml(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def _abstract_from_article(article):
    parts = []
    for node in article.findall(".//Abstract/AbstractText"):
        label = node.attrib.get("Label", "")
        txt = _strip_xml("".join(node.itertext()))
        if txt:
            parts.append(f"{label}: {txt}" if label else txt)
    return " ".join(parts)


def _publication_year(article):
    for path in [
        ".//PubDate/Year",
        ".//ArticleDate/Year",
        ".//PubDate/MedlineDate",
    ]:
        node = article.find(path)
        if node is not None and node.text:
            m = re.search(r"(19|20)\d{2}", node.text)
            if m:
                return m.group(0)
    return "Not stated"


def _authors(article):
    names = []
    for a in article.findall(".//AuthorList/Author"):
        collective = a.findtext("CollectiveName")
        if collective:
            names.append(collective)
            continue
        last = a.findtext("LastName") or ""
        initials = a.findtext("Initials") or ""
        name = (last + " " + initials).strip()
        if name:
            names.append(name)
    return ", ".join(names[:8])


def _article_ids(article):
    pmid = ""
    pmcid = ""
    doi = ""
    for node in article.findall(".//PubmedData/ArticleIdList/ArticleId"):
        kind = (node.attrib.get("IdType") or "").lower()
        value = (node.text or "").strip()
        if kind == "pubmed":
            pmid = value
        elif kind == "pmc":
            pmcid = value
        elif kind == "doi":
            doi = value
    if not pmid:
        node = article.find(".//MedlineCitation/PMID")
        if node is not None:
            pmid = (node.text or "").strip()
    return pmid, pmcid, doi


def _classify_study(title, abstract, publication_types):
    text = (title + " " + abstract + " " + " ".join(publication_types)).lower()
    labels = []
    if re.search(r"\bin vitro\b|dissolution|release study|permeation|permeability|cell line|caco-2", text):
        labels.append("In-vitro")
    if re.search(r"\bin vivo\b|rat|rats|mouse|mice|rabbit|dog|animal|human subjects|volunteers|patients", text):
        labels.append("In-vivo")
    if re.search(r"pharmacokinetic|\bpk\b|cmax|tmax|auc|bioavailability", text):
        labels.append("PK / bioavailability")
    if re.search(r"bioequivalence|\bbe study\b|test/reference|90% confidence interval", text):
        labels.append("Bioequivalence")
    if re.search(r"formulation|tablet|capsule|microparticle|nanoparticle|liposome|gel|suspension", text):
        labels.append("Formulation")
    return ", ".join(dict.fromkeys(labels)) or "Other / not classifiable from abstract"


def _sentences(text):
    return [x.strip() for x in re.split(r"(?<=[.!?])\s+", text or "") if len(x.strip()) > 25]


def _extract_sentences(text, keywords, limit=5):
    out = []
    for sent in _sentences(text):
        low = sent.lower()
        if any(k in low for k in keywords):
            out.append(sent)
    return out[:limit]


def _extract_numeric_mentions(text, limit=25):
    if not text:
        return []
    # Preserve the exact reported value/unit phrase from the abstract. These are
    # observations, not model-derived ranges.
    patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:%|mg/mL|mg\/kg|mg|g|µg|ug|ng/mL|ng|\u00b5M|uM|nM|mM|h|hr|hours?|min|minutes?|sec|s|\u00b0C|C|mm|nm|\bday[s]?|week[s]?)\b",
        r"\b(?:Cmax|Tmax|AUC(?:0-[^ ,;]+)?|t1/2|half-life|MIC|MBC|EC50|IC50|Papp|flux)\s*(?:=|of|was|were|:)?\s*\d+(?:\.\d+)?\s*[A-Za-zµ%/0-9.\-]+",
        r"\b\d+(?:\.\d+)?\s*(?:to|[-–])\s*\d+(?:\.\d+)?\s*[A-Za-zµ%/0-9.\-]+",
    ]
    found = []
    for pattern in patterns:
        for m in re.finditer(pattern, text, flags=re.I):
            val = m.group(0).strip()
            if val not in found:
                found.append(val)
            if len(found) >= limit:
                return found
    return found


def _extract_study_fields(title, abstract):
    text = abstract or ""
    lower = text.lower()
    model = _extract_sentences(text, [
        "healthy volunteer", "healthy volunteers", "patient", "patients", "rat", "rats", "mouse", "mice",
        "rabbit", "rabbits", "dog", "dogs", "caco-2", "cell line", "cells", "animal model", "human"
    ], 4)
    design = _extract_sentences(text, [
        "randomized", "randomised", "crossover", "cross-over", "parallel", "open-label", "double-blind",
        "single-dose", "multiple-dose", "in vitro", "ex vivo", "in vivo", "comparative", "stability study"
    ], 4)
    formulation = _extract_sentences(text, [
        "formulation", "tablet", "capsule", "suspension", "solution", "gel", "cream", "microparticle",
        "nanoparticle", "liposome", "solid dispersion", "granule", "matrix", "release"
    ], 5)
    endpoints = _extract_sentences(text, [
        "dissolution", "release", "permeability", "permeation", "assay", "content uniformity", "cmax", "tmax",
        "auc", "half-life", "bioavailability", "bioequivalence", "mic", "mbc", "stability", "degradation",
        "adverse", "safety", "efficacy", "pain score", "platelet"
    ], 7)
    results = _extract_sentences(text, [
        "significantly", "significant", "increased", "decreased", "higher", "lower", "greater", "reduced",
        "resulted", "showed", "demonstrated", "found", "improved", "similar", "equivalent", "difference"
    ], 8)
    excipient_terms = [
        "lactose", "microcrystalline cellulose", "mannitol", "starch", "povidone", "crospovidone", "croscarmellose",
        "magnesium stearate", "colloidal silicon dioxide", "silicon dioxide", "hypromellose", "HPMC", "PEG",
        "poloxamer", "carbopol", "carbomer", "sodium lauryl sulfate", "sodium starch glycolate", "talc",
        "ethylcellulose", "cellulose acetate", "pva", "pvp", "hydroxypropyl methylcellulose"
    ]
    excipients = [x for x in excipient_terms if x.lower() in lower]
    dose_sentences = _extract_sentences(text, ["dose", "mg", "mg/kg", "administered", "oral", "intravenous", "topical"], 5)
    return {
        "Model / population evidence": " ".join(model) if model else "Not stated in abstract",
        "Study design evidence": " ".join(design) if design else "Not stated in abstract",
        "Formulation / intervention evidence": " ".join(formulation) if formulation else "Not stated in abstract",
        "Endpoints / parameters reported": " ".join(endpoints) if endpoints else "Not stated in abstract",
        "Reported result evidence": " ".join(results) if results else "Not stated in abstract",
        "Dose / route evidence": " ".join(dose_sentences) if dose_sentences else "Not stated in abstract",
        "Excipient/material names detected": ", ".join(excipients) if excipients else "No common excipient term detected in abstract",
        "Numeric findings reported": "; ".join(_extract_numeric_mentions(text)) or "No numeric value detected in abstract",
    }


@st.cache_data(ttl=21600, show_spinner=False)
def pubmed_search_ids(query, retmax=20):
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {"db": "pubmed", "term": query, "retmode": "json", "retmax": int(retmax), "sort": "relevance"}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return []
        return r.json().get("esearchresult", {}).get("idlist", [])
    except Exception:
        return []


@st.cache_data(ttl=21600, show_spinner=False)
def pubmed_fetch_records(pmids):
    if not pmids:
        return []
    url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    try:
        r = requests.get(url, params={"db": "pubmed", "id": ",".join(pmids), "retmode": "xml"}, timeout=40)
        if r.status_code != 200:
            return []
        import xml.etree.ElementTree as ET
        root = ET.fromstring(r.text)
        records = []
        for article in root.findall(".//PubmedArticle"):
            title_node = article.find(".//ArticleTitle")
            title = _strip_xml("".join(title_node.itertext())) if title_node is not None else "Untitled"
            abstract = _abstract_from_article(article)
            journal = article.findtext(".//Journal/Title") or "Not stated"
            pmid, pmcid, doi = _article_ids(article)
            pub_types = [x.text.strip() for x in article.findall(".//PublicationTypeList/PublicationType") if x.text]
            year = _publication_year(article)
            authors = _authors(article)
            fields = _extract_study_fields(title, abstract)
            records.append({
                "PMID": pmid,
                "PMCID": pmcid,
                "DOI": doi,
                "Title": title,
                "Journal": journal,
                "Year": year,
                "Authors": authors,
                "Publication types": ", ".join(pub_types),
                "Study type": _classify_study(title, abstract, pub_types),
                "Abstract": abstract or "Abstract not available",
                **fields,
            })
        return records
    except Exception:
        return []


def get_actual_literature(name, max_each=15):
    # Two complementary searches reduce the chance that an in-vitro-only or
    # in-vivo-only paper is missed by one broad query.
    q_invitro = f'"{name}" AND ("in vitro" OR dissolution OR permeability OR permeation OR "drug release" OR formulation)'
    q_invivo = f'"{name}" AND ("in vivo" OR pharmacokinetic OR bioavailability OR bioequivalence OR pharmacodynamic)'
    ids = []
    for q in [q_invitro, q_invivo]:
        for pmid in pubmed_search_ids(q, max_each):
            if pmid not in ids:
                ids.append(pmid)
    return pubmed_fetch_records(ids[: max_each * 2])


@st.cache_data(ttl=86400, show_spinner=False)
def get_pmc_fulltext_sections(pmcid):
    """Fetch open-access PMC full text through NCBI BioC, when available."""
    if not pmcid:
        return {"status": "No PMCID is attached to this record.", "methods": [], "results": [], "other": []}
    pmc = str(pmcid).strip()
    if not pmc.startswith("PMC"):
        pmc = "PMC" + pmc
    url = f"https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/{pmc}/unicode"
    try:
        response = requests.get(url, timeout=25, headers={"User-Agent": "PharmaLens educational research dashboard"})
        if response.status_code != 200:
            return {"status": f"Open-access full text not available through PMC BioC (HTTP {response.status_code}).", "methods": [], "results": [], "other": []}
        payload = response.json()
        documents = payload if isinstance(payload, list) else payload.get("documents", [])
        passages = []
        for doc in documents:
            for passage in doc.get("passages", []):
                text_value = (passage.get("text") or "").strip()
                infons = passage.get("infons") or {}
                section = str(infons.get("section_type") or infons.get("section") or infons.get("type") or "").lower()
                if text_value:
                    passages.append((section, text_value))
        methods = [t for sec, t in passages if any(k in sec for k in ["methods", "materials", "experimental", "study design", "methodology"]) ]
        results = [t for sec, t in passages if any(k in sec for k in ["results", "discussion", "conclusion"]) ]
        other = [t for sec, t in passages if not any(k in sec for k in ["methods", "materials", "experimental", "study design", "methodology", "results", "discussion", "conclusion"]) ]
        if not methods and not results and not passages:
            return {"status": "PMC returned no parseable full-text passages.", "methods": [], "results": [], "other": []}
        return {"status": "Open-access full text retrieved. Section labels depend on the article's XML structure.", "methods": methods[:100], "results": results[:100], "other": other[:30]}
    except Exception as exc:
        return {"status": f"Could not retrieve full text: {type(exc).__name__}", "methods": [], "results": [], "other": []}


@st.cache_data(ttl=21600, show_spinner=False)
def get_objective_literature(name, objective, stream, max_results=20):
    """Search PubMed for an API + therapeutic objective + study stream."""
    objective_terms = {
        "Analgesic / pain relief": '(analgesic OR analgesia OR antinociceptive OR pain OR nociception)',
        "Antipyretic / fever reduction": '(antipyretic OR fever OR pyrexia OR hyperthermia OR body temperature)',
        "Anti-inflammatory": '(anti-inflammatory OR inflammation OR prostaglandin OR cyclooxygenase)',
        "Pharmacokinetics / bioavailability": '(pharmacokinetic OR Cmax OR Tmax OR AUC OR bioavailability)',
        "Bioequivalence": '(bioequivalence OR bioequivalent OR "test reference" OR ANDA)',
        "Formulation / dissolution": '(formulation OR dissolution OR "drug release" OR excipient OR stability)',
        "Antimicrobial activity": '(antimicrobial OR antibacterial OR MIC OR MBC OR susceptibility)',
        "General pharmacology / safety": '(pharmacology OR safety OR toxicology OR adverse events)',
    }
    stream_terms = {
        "In-vitro": '("in vitro" OR cell OR cellular OR enzyme OR assay OR dissolution OR permeability OR permeation)',
        "In-vivo / animal": '("in vivo" OR animal OR mice OR mouse OR rats OR rat OR rabbit OR fever OR pain model)',
        "Human / clinical": '(human OR clinical OR patients OR volunteers OR randomized OR crossover)',
        "All study types": '(study OR evaluation OR analysis OR trial OR formulation)',
    }
    q = f'"{name}" AND {objective_terms.get(objective, "(pharmacology OR formulation)")} AND {stream_terms.get(stream, "(study)")}'
    ids = pubmed_search_ids(q, max_results)
    return pubmed_fetch_records(ids)


@st.cache_data(ttl=21600, show_spinner=False)
def get_orange_book_products(name):
    """Return current public FDA Orange Book product records for an API.

    The endpoint is public and does not require an API key for ordinary queries.
    The app treats the result as regulatory evidence, not as a blanket claim
    that every product is generic or therapeutically equivalent.
    """
    url = "https://api.fda.gov/drug/orangebook.json"
    params = {"search": f'products.active_ingredients.name:"{name.upper()}"', "limit": 99}
    try:
        r = requests.get(url, params=params, timeout=30)
        if r.status_code != 200:
            return []
        results = r.json().get("results", [])
        rows = []
        for rec in results:
            app_no = rec.get("application_number", "")
            app_type = rec.get("application_type", "")
            sponsor = rec.get("sponsor_name", "")
            for product in rec.get("products", []) or []:
                active = product.get("active_ingredients", []) or []
                names = ", ".join(str(x.get("name", "")) for x in active if x.get("name"))
                strengths = ", ".join(str(x.get("strength", "")) for x in active if x.get("strength"))
                rows.append({
                    "Application": app_no,
                    "Application type": app_type,
                    "Sponsor": sponsor,
                    "Ingredient": names or name,
                    "Strength": strengths,
                    "Dosage form": product.get("dosage_form", ""),
                    "Route": ", ".join(product.get("route", []) or []),
                    "Marketing status": product.get("marketing_status", ""),
                    "Product number": product.get("product_number", ""),
                    "Reference drug": product.get("reference_drug", ""),
                    "Reference standard": product.get("reference_standard", ""),
                    "TE code": product.get("te_code", ""),
                })
        return rows
    except Exception:
        return []


def evidence_summary(records):
    if not records:
        return {}
    buckets = {
        "Study types": {},
        "Parameters / endpoints": {},
        "Materials / excipients detected": {},
    }
    for rec in records:
        for label in [x.strip() for x in rec["Study type"].split(",") if x.strip()]:
            buckets["Study types"][label] = buckets["Study types"].get(label, 0) + 1
        for x in rec["Endpoints / parameters reported"].split(" "):
            pass
        # Keep the exact evidence snippets rather than inventing a numerical range.
    return buckets

st.markdown("""<div class="hero"><h1>💊 PharmaLens 100</h1><p>API properties, dosage forms, product-label ingredients, formulation development, manufacturing risk and research-study intelligence.</p></div>""",unsafe_allow_html=True)
st.markdown("""<div class="notice"><b>Research-intelligence notice:</b> PharmaLens retrieves live public literature and regulatory records and extracts evidence from them. It reduces source-hunting, but it does not replace the original publication, official label or regulatory record for final academic/regulatory decisions.</div>""",unsafe_allow_html=True)

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

tabs=st.tabs(["🧬 API profile","🌐 Live properties","🧪 Exact ingredients","🔬 Research Intelligence","🏛️ Regulatory Intelligence","🏭 Process defects","📋 Development notes"])

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
    st.subheader(f"🔬 Actual research intelligence: {selected_name}")
    st.markdown(
        """<div class="success-box"><b>What this module does:</b> it searches PubMed live, retrieves actual indexed paper metadata and abstracts, classifies studies, supports objective-specific searches (for example analgesic vs antipyretic), and extracts the parameters, models, formulations, doses and numeric findings explicitly reported in those abstracts. It is designed to reduce literature-hunting, while keeping the original PMID/source available for verification.</div>""",
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    with c1:
        paper_limit = st.selectbox("Papers per study stream", [5, 10, 15, 20, 25], index=2)
    with c2:
        st.metric("Research source", "PubMed / NCBI")
    with c3:
        st.metric("Selected API", selected_name)

    if st.button("🔎 Fetch actual in-vitro + in-vivo studies", type="primary", use_container_width=True):
        with st.spinner("Searching PubMed and extracting study evidence..."):
            records = get_actual_literature(selected_name, paper_limit)
        st.session_state[f"research_{selected_name}"] = records

    records = st.session_state.get(f"research_{selected_name}", [])

    if records:
        invitro = [r for r in records if "In-vitro" in r["Study type"]]
        invivo = [r for r in records if "In-vivo" in r["Study type"] or "PK / bioavailability" in r["Study type"] or "Bioequivalence" in r["Study type"]]
        st.write("### Evidence overview")
        a, b, c, d = st.columns(4)
        with a: st.metric("Papers retrieved", len(records))
        with b: st.metric("In-vitro evidence", len(invitro))
        with c: st.metric("In-vivo / PK / BE", len(invivo))
        with d: st.metric("With abstracts", sum(bool(r["Abstract"] and r["Abstract"] != "Abstract not available") for r in records))

        st.write("### 📊 Actual-study evidence matrix")
        matrix = []
        for r in records:
            matrix.append({
                "Year": r["Year"],
                "Study type": r["Study type"],
                "Paper": r["Title"],
                "Model / population": r["Model / population evidence"],
                "Formulation / intervention": r["Formulation / intervention evidence"],
                "Parameters / endpoints": r["Endpoints / parameters reported"],
                "Numeric findings": r["Numeric findings reported"],
                "PMID": r["PMID"],
            })
        st.dataframe(pd.DataFrame(matrix), use_container_width=True, hide_index=True)

        st.write("### 📚 Paper-by-paper research cards")
        for i, r in enumerate(records, start=1):
            with st.expander(f"{i}. {r['Title']}  |  {r['Year']}  |  {r['Study type']}"):
                st.markdown(f"**Journal:** {r['Journal']}  ")
                st.markdown(f"**Authors:** {r['Authors'] or 'Not stated'}  ")
                st.markdown(f"**PMID:** [{r['PMID']}]({_pubmed_url(r['PMID'])})  ")
                if r["DOI"]:
                    st.markdown(f"**DOI:** [{r['DOI']}]({_doi_url(r['DOI'])})  ")
                if r["PMCID"]:
                    st.markdown(f"**PMC:** {r['PMCID']}")
                details = pd.DataFrame([
                    ["Study classification", r["Study type"]],
                    ["Model / population", r["Model / population evidence"]],
                    ["Study design", r["Study design evidence"]],
                    ["Formulation / intervention", r["Formulation / intervention evidence"]],
                    ["Dose / route", r["Dose / route evidence"]],
                    ["Parameters / endpoints", r["Endpoints / parameters reported"]],
                    ["Actual result evidence", r["Reported result evidence"]],
                    ["Numeric findings / ranges explicitly reported", r["Numeric findings reported"]],
                    ["Excipient/material terms detected", r["Excipient/material names detected"]],
                ], columns=["Field", "Evidence extracted from abstract"])
                st.dataframe(details, use_container_width=True, hide_index=True)
                st.write("**Abstract:**")
                st.write(r["Abstract"])

        st.info("Numeric values above are copied/extracted from the indexed abstract text. A blank field means the abstract did not state it. The app does not invent a range when a paper does not report one.")
    else:
        st.info("Press the button above to fetch actual papers. The search uses NCBI PubMed E-utilities and retrieves live indexed records rather than a hand-written list.")

    st.divider()
    st.write("## 🧭 Study map by therapeutic objective")
    st.markdown(
        "Choose *why* the API is being studied first. PharmaLens will then show relevant study families, assays/models, the measurements typically collected, and a targeted live PubMed search. The guide below is a **study-planning map**, not a claim that every method has been used for this API. Where a PubMed record links to a PMC open-access article, a button can also retrieve its Methods and Results sections. Exact animal strain, dose, sample size, assay conditions and numeric ranges must come from the cited paper or approved protocol."
    )

    objective_options = [
        "Analgesic / pain relief", "Antipyretic / fever reduction", "Anti-inflammatory",
        "Pharmacokinetics / bioavailability", "Bioequivalence", "Formulation / dissolution",
        "Antimicrobial activity", "General pharmacology / safety"
    ]
    selected_objective = st.selectbox(
        "1) What effect or research question are you investigating?",
        objective_options,
        key=f"objective_{selected_name}"
    )
    stream_options = ["In-vitro", "In-vivo / animal", "Human / clinical", "All study types"]
    selected_stream = st.selectbox(
        "2) Which evidence stream?", stream_options, key=f"stream_{selected_name}"
    )

    # Method guide: candidate methods are explicitly labelled as commonly used
    # model families, not as confirmed methods for every API/paper.
    assay_catalog = {
        "Analgesic / pain relief": {
            "In-vitro / mechanistic assays": [
                ["COX-1 / COX-2 enzyme activity", "Enzyme inhibition / activity; IC50 only if measured; assay format, enzyme source, substrate and controls", "Mechanistic screening; not a stand-alone demonstration of clinical analgesia"],
                ["Prostaglandin E2 (PGE2) measurement", "PGE2 concentration, inhibition versus control, sampling time, biological matrix, assay kit/platform", "Used where the hypothesis involves prostaglandin pathways; not universal for paracetamol"],
                ["Cell-based inflammatory mediator assays", "Cell type, stimulus, viability/cytotoxicity control, mediator concentration, exposure duration", "Cell model and mediator must be taken from the selected paper"],
            ],
            "In-vivo / animal models": [
                ["Acetic-acid-induced writhing", "Species/strain/sex/weight, test and comparator groups, dose/route, observation window, writhes, % inhibition", "Common peripheral nociception model; not specific proof of a single mechanism"],
                ["Hot-plate test", "Species/strain, baseline and post-dose latency, cut-off time, time points, comparator, response definition", "Thermal nociception; response latency and cut-off are protocol-specific"],
                ["Tail-flick test", "Species/strain, baseline and post-dose latency, stimulus setting, cut-off, time course", "Thermal reflex model; only display as relevant if the paper uses it"],
                ["Formalin test", "Species, early/late phase scoring, licking/biting duration, dose/route, observation schedule", "Different phases may reflect different components of pain behaviour"],
            ],
        },
        "Antipyretic / fever reduction": {
            "In-vitro / mechanistic assays": [
                ["PGE2 pathway / mediator assay", "PGE2 concentration, biological matrix, assay method, baseline/control, time point", "Mechanistic support only; fever reduction itself is usually assessed in a physiological model"],
                ["COX / prostaglandin-pathway assays", "Enzyme or pathway endpoint, assay conditions, concentration-response, IC50 if reported", "Do not assume this alone predicts antipyretic effect"],
            ],
            "In-vivo / animal models": [
                ["Yeast-induced pyrexia model", "Species/strain/sex/age/weight, fever induction method, baseline temperature, dose/route, rectal/core temperature, time points, temperature change", "A commonly reported antipyretic model; exact induction procedure and ranges are study-specific"],
                ["LPS-induced fever model", "Species/strain, LPS source/dose, temperature baseline/time course, intervention timing, controls", "Inflammatory fever model; include only when the paper reports it"],
                ["Vaccine-induced pyrexia model", "Species, vaccine/inducer details, baseline and serial temperature, dose/route, comparator", "Model applicability and ethics approval must be assessed for the specific study"],
            ],
        },
        "Anti-inflammatory": {
            "In-vitro / mechanistic assays": [
                ["COX / LOX enzyme assays", "Enzyme activity, concentration-response, IC50 if reported, controls", "The selected paper determines enzyme source and assay chemistry"],
                ["Cytokine / mediator assays", "TNF-α, IL-1β, IL-6 or other specified mediator; matrix, method, time point", "Only include mediators actually measured in the paper"],
            ],
            "In-vivo / animal models": [
                ["Carrageenan-induced paw edema", "Species/strain, paw-volume/thickness measurement, baseline, time points, dose/route, % inhibition", "A model family for inflammatory edema; not automatically relevant to every API"],
            ],
        },
        "Pharmacokinetics / bioavailability": {
            "In-vitro / analytical methods": [
                ["Bioanalytical method validation", "Analyte/internal standard, selectivity, calibration range, accuracy, precision, recovery, matrix effect, LLOQ, stability", "Use validated method values from the relevant publication or regulated method"],
                ["Dissolution / release testing", "Dosage form, medium and pH, apparatus, rpm, temperature, sampling times, assay method, % dissolved", "Conditions vary by product and applicable monograph/method"],
            ],
            "In-vivo / human or animal studies": [
                ["Pharmacokinetic study", "Cmax, Tmax, AUC interval, t½, clearance and Vd when reported; dose, route, sampling schedule, population/species", "Not every parameter is estimable/reported in every study"],
                ["Absolute / relative bioavailability", "AUC-based comparison, route/formulation, dose normalization where applicable, variability and confidence intervals", "Interpretation depends on study design and route"],
            ],
        },
        "Bioequivalence": {
            "In-vitro / supporting tests": [
                ["Comparative dissolution", "Media/pH, apparatus/rpm, sampling schedule, % dissolved, profile similarity metric if used", "Similarity methods and criteria depend on the applicable guidance/product"],
            ],
            "Human / clinical studies": [
                ["Pharmacokinetic bioequivalence", "Test/reference products, fasting/fed status, design, washout, Cmax and AUC endpoints, geometric mean ratio, 90% CI", "Do not apply a universal acceptance range without checking the current jurisdiction-specific guidance and product-specific rules"],
            ],
        },
        "Formulation / dissolution": {
            "In-vitro tests": [
                ["Dissolution / drug release", "Medium, pH, apparatus, rpm, temperature, time points, filtration, analytical method, % release", "Use conditions from the product-specific method or cited study"],
                ["Assay / content uniformity", "Assay method, individual-unit results, mean, SD/RSD, acceptance criteria and pharmacopeial version", "Official acceptance criteria depend on product and current compendial/regulatory requirements"],
                ["Drug-excipient compatibility", "DSC, FTIR, XRPD or other selected method; storage condition; degradation/interaction signal", "Screening methods do not by themselves prove long-term compatibility"],
                ["Stability study", "Temperature/RH/light condition, duration, assay, impurities, dissolution, appearance, packaging", "Accelerated/long-term conditions and limits must follow the relevant guidance"],
            ],
            "In-vivo / performance": [
                ["PK / comparative performance", "Cmax, Tmax, AUC and other pre-specified endpoints; formulation, dose, route, design", "Required only when justified by the product and development question"],
            ],
        },
        "Antimicrobial activity": {
            "In-vitro microbiology": [
                ["MIC / MBC", "Organism/strain, inoculum, medium, incubation conditions, MIC and MBC, controls", "Follow the appropriate current microbiology standard; values depend on organism and method"],
                ["Zone of inhibition", "Organism, medium, inoculum, disc/well content, incubation and zone diameter", "Not interchangeable with MIC without a validated interpretation framework"],
            ],
            "In-vivo / clinical": [
                ["Infection model / clinical outcome", "Organism, model/population, dose/route, microbiological endpoint, clinical endpoint, safety", "Only use when supported by the actual study and ethical/regulatory approval"],
            ],
        },
        "General pharmacology / safety": {
            "In-vitro safety / mechanism": [
                ["Cytotoxicity / cell viability", "Cell type, exposure time, concentration range, viability readout, positive/negative controls", "Cell viability is not equivalent to whole-organism safety"],
            ],
            "In-vivo / clinical safety": [
                ["Safety / tolerability monitoring", "Species/population, exposure, clinical observations, lab parameters, adverse events, observation duration", "Endpoints and stopping rules must follow approved protocol and applicable guidance"],
            ],
        },
    }

    if selected_name == "Paracetamol":
        st.info("Paracetamol focus: choose Analgesic for pain-related endpoints or Antipyretic for fever-related endpoints. A method shown below is a candidate method family; the paper cards/search results determine which methods were actually used for paracetamol.")
    chosen_methods = assay_catalog.get(selected_objective, {})
    visible_groups = list(chosen_methods.items())
    if selected_stream == "In-vitro":
        visible_groups = [(k, v) for k, v in visible_groups if "In-vitro" in k or "In-vitro" in k or "In-vitro" in k]
    elif selected_stream == "In-vivo / animal":
        visible_groups = [(k, v) for k, v in visible_groups if "In-vivo" in k]
    elif selected_stream == "Human / clinical":
        visible_groups = [(k, v) for k, v in visible_groups if "Human" in k or "clinical" in k.lower()]

    if not visible_groups:
        st.caption("No separate guide group is configured for this stream/objective. Use All study types or run the targeted literature search below.")
    for group_name, methods in visible_groups:
        st.write(f"### {group_name}")
        st.dataframe(pd.DataFrame(methods, columns=["Assay / model", "Parameters to capture", "Interpretation / limitation"]), use_container_width=True, hide_index=True)

    # Explicit study workspace: requirements, results, pharmacological effect, visual/video.
    st.divider()
    st.write("## 🧪 In-vitro / In-vivo Studies: Study Workspace")
    st.caption("Select the exact candidate study to see what must be recorded. Candidate requirements are a planning checklist; actual methods/results must be sourced from a retrieved paper or approved protocol.")

    candidate_rows = []
    for group_name, methods in chosen_methods.items():
        for row in methods:
            # row = method/model, parameters, interpretation
            if selected_stream == "All study types" or selected_stream.lower().replace(" / animal", "") in group_name.lower() or (selected_stream == "Human / clinical" and "human" in group_name.lower()):
                candidate_rows.append({"Study group": group_name, "Particular study / assay": row[0], "Parameters / requirements": row[1], "Pharmacological context": row[2]})
    if not candidate_rows:
        for group_name, methods in chosen_methods.items():
            for row in methods:
                candidate_rows.append({"Study group": group_name, "Particular study / assay": row[0], "Parameters / requirements": row[1], "Pharmacological context": row[2]})

    study_tabs = st.tabs(["1️⃣ Study requirements", "2️⃣ Actual results", "3️⃣ Pharmacological effect", "4️⃣ Diagram & video"])
    with study_tabs[0]:
        if candidate_rows:
            study_names = [f"{r['Study group']} — {r['Particular study / assay']}" for r in candidate_rows]
            chosen_study_idx = st.selectbox("Choose a particular study", range(len(study_names)), format_func=lambda i: study_names[i], key=f"particular_study_{selected_name}_{selected_objective}_{selected_stream}")
            chosen_study = candidate_rows[chosen_study_idx]
            st.markdown(f"### {chosen_study['Particular study / assay']}")
            st.write("**Study type / group:**", chosen_study["Study group"])
            st.write("**Requirements and parameters to capture:**")
            param_items = [x.strip() for x in re.split(r"[,;]", chosen_study["Parameters / requirements"]) if x.strip()]
            if param_items:
                st.dataframe(pd.DataFrame({"Parameter to capture": param_items, "Why it matters": ["Record the exact value, units and method from the selected study" for _ in param_items]}), use_container_width=True, hide_index=True)
            st.write("**Study-specific requirements: materials, model and instrumentation**")
            study_lower = chosen_study["Particular study / assay"].lower()
            requirements = [
                ("Test material", f"{selected_name} API; salt/grade, batch, formulation and vehicle exactly as reported"),
                ("Model / biological material", "For in-vivo: species, strain, sex, age, body weight, source and acclimatization. For in-vitro: cell line/tissue/enzyme source, passage or preparation details"),
                ("Animals / subjects", "Species and number per group, inclusion criteria, randomization, housing and ethics approval; if no animal/human model is used, mark not applicable"),
                ("Controls / comparator", "Vehicle/negative control, positive control or reference treatment, and untreated/baseline control as relevant"),
                ("Dose / concentration", "Dose levels, units, route, dosing frequency, treatment duration, timing and rationale as reported in the source"),
                ("Equipment / instruments", "Exact instrument, model, manufacturer, calibration and settings used for the chosen assay; examples depend on method"),
                ("Reagents / solutions", "Reagent/kit names, grade, supplier, buffer/solvent composition, pH, concentration, preparation and storage when reported"),
                ("Assay-specific items", "For COX/PGE2: enzyme/substrate or PGE2 kit and detection platform. For writhing/formalin/hot-plate/tail-flick: validated apparatus, stimulus settings and observation sheet. For fever model: temperature probe/thermometer and induction agent details. Confirm exact items from paper"),
                ("Measurements / time points", "Baseline, sampling/observation schedule, endpoint definition, units and stopping/cut-off criteria"),
                ("Data quality / statistics", "Replicates or group size, mean and variability, statistical test, significance threshold and exclusion criteria"),
                ("Safety / compliance", "Institutional animal ethics approval and approved protocol for animal studies; trained supervision and applicable biosafety requirements")
            ]
            st.dataframe(pd.DataFrame(requirements, columns=["Requirement category", "Information needed for this study"]), use_container_width=True, hide_index=True)
            st.info("These are study-planning requirements. The exact animal strain, apparatus model, reagent brand, solution recipe and experimental settings must be transcribed from the historical paper/protocol; they are not universal across studies.")
            st.write("**Interpretation / limitation:**", chosen_study["Pharmacological context"])
        else:
            st.info("No candidate assay guide is configured for this objective. Choose another objective or All study types.")

    with study_tabs[1]:
        st.markdown("### Actual results from past studies")
        st.caption("Dose is selected first. Results shown below are filtered from actual retrieved PubMed records and their available abstract/full-text evidence; no dose-response result is invented.")
        obj_records_for_result = st.session_state.get(f"objective_records_{selected_name}", [])
        obj_key_for_result = st.session_state.get(f"objective_records_key_{selected_name}")
        if obj_records_for_result and obj_key_for_result == (selected_objective, selected_stream):
            dose_pattern = re.compile(r"(?<![A-Za-z])\d+(?:\.\d+)?\s*(?:µg|μg|mcg|mg|g|ng|mmol|µmol|μmol|mol)(?:\s*/\s*(?:kg|mL|ml|L|day|d|h|hour|dose|animal|subject))?", re.I)
            dose_map = {}
            for rec in obj_records_for_result:
                dose_text = " ".join([str(rec.get("Dose / route evidence", "")), str(rec.get("Abstract", "")), str(rec.get("Numeric findings reported", ""))])
                found = sorted(set(m.group(0).strip() for m in dose_pattern.finditer(dose_text)))
                for dose in found:
                    dose_map.setdefault(dose, []).append(rec)
            dose_options = ["All reported doses / dose not explicit in indexed text"] + sorted(dose_map.keys(), key=str.lower)
            chosen_dose = st.selectbox("1) Select dose reported in past studies", dose_options, key=f"result_dose_{selected_name}_{selected_objective}_{selected_stream}")
            if chosen_dose == dose_options[0]:
                dose_records = obj_records_for_result
                st.caption("Showing all matching records, including papers where the dose was not stated in the abstract.")
            else:
                dose_records = dose_map.get(chosen_dose, [])
                st.caption(f"Showing historical records whose indexed text contains the selected dose: {chosen_dose}. Similar units or doses are not converted automatically.")
            if dose_records:
                result_rows = []
                for rec in dose_records:
                    result_rows.append({"Selected dose filter": chosen_dose, "Paper": rec.get("Title", "Not stated"), "Year": rec.get("Year", "Not stated"), "Study model / animal / population": rec.get("Model / population evidence", "Not stated in available text"), "Assay / equipment / parameters": rec.get("Endpoints / parameters reported", "Not stated in available text"), "Dose / route evidence": rec.get("Dose / route evidence", "Not stated in available text"), "Actual reported result": rec.get("Reported result evidence", "Not stated in available text"), "Numeric findings as reported": rec.get("Numeric findings reported", "Not stated in available text"), "PMID": rec.get("PMID", "")})
                st.dataframe(pd.DataFrame(result_rows), use_container_width=True, hide_index=True)
                for i, rec in enumerate(dose_records, 1):
                    with st.expander(f"{i}. {rec.get('Title', 'Untitled paper')} · {rec.get('Year', '')} · PMID {rec.get('PMID', '')}"):
                        st.write("**Study model / animal / population:**", rec.get("Model / population evidence", "Not stated in available text"))
                        st.write("**Study design:**", rec.get("Study design evidence", "Not stated in available text"))
                        st.write("**Formulation / intervention:**", rec.get("Formulation / intervention evidence", "Not stated in available text"))
                        st.write("**Dose / route:**", rec.get("Dose / route evidence", "Not stated in available text"))
                        st.write("**Assays / endpoints:**", rec.get("Endpoints / parameters reported", "Not stated in available text"))
                        st.write("**Actual result evidence:**", rec.get("Reported result evidence", "Not stated in available text"))
                        st.write("**Numeric values exactly detected:**", rec.get("Numeric findings reported", "Not stated in available text"))
                        st.write("**Abstract:**", rec.get("Abstract", "Abstract not available"))
                        st.markdown(f"**Source:** [{rec.get('PMID', 'PubMed record')}]({_pubmed_url(rec['PMID'])})")
            else:
                st.info("No indexed record matched that exact dose string. Choose another reported dose or the all-records option. The app does not estimate missing outcomes.")
        else:
            st.info("Loading historical study evidence automatically for this API, objective and study type…")
        st.markdown("### Result fields captured separately")
        st.dataframe(pd.DataFrame([
            ["Dose / concentration", "Exact reported value + units"], ["Animal / cell / population", "Species/strain/cell line/participants as reported"], ["Assay / model", "Exact method name"], ["Equipment", "Instrument/apparatus and settings if reported"], ["Reagents / solutions", "Reagent, buffer, vehicle, concentration and pH if reported"], ["Primary endpoint", "Measured outcome + units"], ["Time points", "Actual observation/sampling times"], ["Results", "Reported value, group comparison and statistics"], ["Reference", "PMID/DOI and article link"]
        ], columns=["Result field", "What PharmaLens captures"]), use_container_width=True, hide_index=True)

    with study_tabs[2]:
        st.markdown("### Pharmacological effect")
        st.write(f"**Selected API:** {selected_name}")
        st.write(f"**Research objective:** {selected_objective}")
        st.write(f"**API profile indication/context:** {selected_drug.get('uses', 'Not available')}")
        effect_explainer = {
            "Analgesic / pain relief": "Analgesic effect means reduction of pain-related responses. Animal behaviour models and mechanistic assays provide different kinds of evidence and should not be treated as equivalent to human clinical benefit.",
            "Antipyretic / fever reduction": "Antipyretic effect means reduction of elevated body temperature during fever. In-vitro pathway assays may support a mechanism, while temperature change is assessed in a suitable physiological model or clinical study.",
            "Anti-inflammatory": "Anti-inflammatory effect concerns reduction of inflammatory processes or endpoints. The specific mediator, tissue/model and endpoint must match the paper.",
            "Pharmacokinetics / bioavailability": "PK describes concentration over time and parameters such as Cmax, Tmax and AUC when measurable. It describes exposure, not by itself therapeutic efficacy.",
            "Bioequivalence": "Bioequivalence compares exposure/performance of test and reference products using the applicable study design and jurisdiction-specific criteria.",
            "Formulation / dissolution": "These studies assess product quality/performance, such as release, assay, content uniformity or stability. In-vitro similarity alone does not always establish in-vivo equivalence.",
            "Antimicrobial activity": "Antimicrobial studies measure effects against specified organisms using methods such as MIC/MBC or clinical/microbiological outcomes; interpretation depends on organism and method.",
            "General pharmacology / safety": "Safety and general pharmacology assess specified biological effects and adverse findings in a defined model/population; results cannot be generalized beyond their evidence."
        }
        st.info(effect_explainer.get(selected_objective, "Interpret the effect only within the study's defined endpoint and model."))
        st.write("**Candidate endpoint guide:**")
        for group_name, methods in chosen_methods.items():
            for method in methods:
                st.markdown(f"- **{method[0]}:** {method[1]}")
        st.caption("This section explains the pharmacological concept. Actual efficacy, effect size and statistical significance must come from the retrieved study results, not from this general guide.")

    with study_tabs[3]:
        st.markdown("### Study workflow diagram")
        diagram_html = f"""<div style="font-family:Arial,sans-serif;text-align:center;background:#f8fafc;padding:18px;border-radius:14px;color:#0f172a"><div style="background:#dbeafe;padding:12px;border-radius:10px;font-weight:bold">API: {selected_name}</div><div style="font-size:24px;padding:4px">↓</div><div style="background:#ccfbf1;padding:12px;border-radius:10px;font-weight:bold">Objective: {selected_objective}</div><div style="font-size:24px;padding:4px">↓</div><div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap"><div style="flex:1;min-width:180px;background:#fef3c7;padding:12px;border-radius:10px"><b>In-vitro</b><br/>Assay / cell / analytical method<br/>Controls + concentrations<br/>Measured endpoint</div><div style="flex:1;min-width:180px;background:#ede9fe;padding:12px;border-radius:10px"><b>In-vivo / human</b><br/>Model / population<br/>Dose + route + time points<br/>Physiological / clinical endpoint</div></div><div style="font-size:24px;padding:4px">↓</div><div style="background:#e2e8f0;padding:12px;border-radius:10px;font-weight:bold">Extract Methods → Parameters → Results → Limitations → PMID/source</div></div>"""
        st.components.v1.html(diagram_html, height=320, scrolling=False)
        st.markdown("### Video / visual learning")
        video_query = quote(f"{selected_name} {selected_objective} pharmacology assay animal model experiment educational")
        st.link_button("▶ Search videos for this API + objective", f"https://www.youtube.com/results?search_query={video_query}", use_container_width=True)
        st.caption("A search link is provided rather than silently embedding an unverified video. If you have a specific public educational video URL, paste it below to play it inside PharmaLens.")
        video_url = st.text_input("Optional: paste a public video URL to play here", key=f"study_video_url_{selected_name}_{selected_objective}", placeholder="https://www.youtube.com/watch?v=...")
        if video_url.strip():
            if video_url.strip().startswith(("https://", "http://")):
                st.video(video_url.strip())
            else:
                st.warning("Enter a complete http:// or https:// video URL.")
        st.warning("Use only approved protocols and qualified supervision for laboratory/animal work. This diagram is a conceptual workflow, not an experimental protocol.")

    objective_limit = 20
    fetch_key = (selected_name, selected_objective, selected_stream, objective_limit)
    existing_fetch_key = st.session_state.get("auto_objective_fetch_key")
    if existing_fetch_key != fetch_key:
        with st.spinner(f"Loading past studies for {selected_name} · {selected_objective} · {selected_stream}…"):
            objective_records = get_objective_literature(selected_name, selected_objective, selected_stream, objective_limit)
        st.session_state[f"objective_records_{selected_name}"] = objective_records
        st.session_state[f"objective_records_key_{selected_name}"] = (selected_objective, selected_stream)
        st.session_state["auto_objective_fetch_key"] = fetch_key

    objective_records = st.session_state.get(f"objective_records_{selected_name}", [])
    objective_key = st.session_state.get(f"objective_records_key_{selected_name}")
    if objective_records and objective_key == (selected_objective, selected_stream):
        st.write(f"### Actual PubMed records: {selected_objective} · {selected_stream}")
        obj_rows = []
        for rec in objective_records:
            obj_rows.append({
                "Year": rec["Year"], "Study type": rec["Study type"], "Title": rec["Title"],
                "Model / population": rec["Model / population evidence"],
                "Assays / endpoints": rec["Endpoints / parameters reported"],
                "Dose / route": rec["Dose / route evidence"],
                "Numeric values actually detected": rec["Numeric findings reported"], "PMID": rec["PMID"]
            })
        st.dataframe(pd.DataFrame(obj_rows), use_container_width=True, hide_index=True)
        for i, rec in enumerate(objective_records, 1):
            with st.expander(f"{i}. {rec['Title']} · PMID {rec['PMID']}"):
                st.write(f"**Journal/year:** {rec['Journal']} · {rec['Year']}")
                st.write(f"**Model/population:** {rec['Model / population evidence']}")
                st.write(f"**Study design:** {rec['Study design evidence']}")
                st.write(f"**Formulation/intervention:** {rec['Formulation / intervention evidence']}")
                st.write(f"**Assays/endpoints:** {rec['Endpoints / parameters reported']}")
                st.write(f"**Dose/route:** {rec['Dose / route evidence']}")
                st.write(f"**Reported results:** {rec['Reported result evidence']}")
                st.write(f"**Numeric values detected in abstract:** {rec['Numeric findings reported']}")
                st.write(f"**Abstract:** {rec['Abstract']}")
                if rec.get("PMCID"):
                    if st.button("📖 Fetch open-access full-text Methods + Results", key=f"fulltext_{selected_name}_{selected_objective}_{selected_stream}_{i}"):
                        with st.spinner("Fetching available PMC full text..."):
                            fulltext = get_pmc_fulltext_sections(rec["PMCID"])
                        st.session_state[f"fulltext_{selected_name}_{selected_objective}_{selected_stream}_{i}"] = fulltext
                    fulltext = st.session_state.get(f"fulltext_{selected_name}_{selected_objective}_{selected_stream}_{i}")
                    if fulltext:
                        st.caption(fulltext["status"])
                        if fulltext["methods"]:
                            with st.expander("Full-text Methods / Materials and Methods"):
                                for para in fulltext["methods"]:
                                    st.write(para)
                        if fulltext["results"]:
                            with st.expander("Full-text Results / Discussion"):
                                for para in fulltext["results"]:
                                    st.write(para)
                        if not fulltext["methods"]:
                            st.info("A separate Methods section was not identified by section labels. The source paper link remains available below.")
                else:
                    st.caption("No PMCID in this PubMed record, so the app cannot fetch a PMC full-text copy through this route. Abstract-only fields may omit methods, exact ranges, animal details or results.")
                st.markdown(f"**Source:** [{rec['PMID']}]({_pubmed_url(rec['PMID'])})")
    elif objective_key == (selected_objective, selected_stream):
        st.warning("No matching records were returned for this exact live query. Try All study types or another objective. This means the current search returned no records, not that no study exists.")

    st.write("### 🔎 Targeted literature searches")
    x, y = st.columns(2)
    with x:
        st.link_button("PubMed: formulation / in-vitro", get_pubmed_search_url(selected_name, "In vitro"), use_container_width=True)
    with y:
        st.link_button("PubMed: in-vivo / PK / BE", get_pubmed_search_url(selected_name, "In vivo"), use_container_width=True)

    st.caption("Source: NCBI PubMed E-utilities. PharmaLens uses the public NCBI search/retrieval service to turn literature records into a structured evidence table.")

with tabs[4]:
    st.subheader(f"🏛️ Regulatory intelligence: {selected_name}")
    st.markdown(
        """<div class="success-box"><b>Goal:</b> bring public regulatory evidence into the same API dashboard. FDA Orange Book data can show approved products, application type, dosage form, route, reference status and TE code; DailyMed provides current submitted labeling; openFDA provides structured label data.</div>""",
        unsafe_allow_html=True,
    )

    if st.button("🏛️ Fetch current FDA regulatory evidence", type="primary", use_container_width=True):
        with st.spinner("Fetching Orange Book + openFDA + DailyMed evidence..."):
            ob = get_orange_book_products(selected_name)
            fd = get_openfda_data(selected_name)
            dm = normalize_dailymed_records(get_dailymed_records(selected_name))
        st.session_state[f"reg_{selected_name}"] = {"orange": ob, "fda": fd, "dailymed": dm}

    reg = st.session_state.get(f"reg_{selected_name}", {})
    orange = reg.get("orange", [])
    fda = reg.get("fda", {})
    dm = reg.get("dailymed", [])

    if orange:
        st.write("### 💊 FDA Orange Book product evidence")
        st.dataframe(pd.DataFrame(orange), use_container_width=True, hide_index=True)
        st.caption("Orange Book records are product-level regulatory evidence. TE codes, reference status and application type must be interpreted in the exact dosage-form/route/strength context.")
    else:
        st.warning("No Orange Book records were returned for this API, or the endpoint was temporarily unavailable.")

    st.write("### 🏷️ openFDA structured label evidence")
    if fda:
        for title, value in fda.items():
            with st.expander(title):
                st.write(value)
    else:
        st.info("Fetch regulatory evidence above to load current openFDA label data.")

    st.write("### 📄 DailyMed label evidence")
    if dm:
        st.dataframe(pd.DataFrame(dm), use_container_width=True, hide_index=True)
    else:
        st.info("No DailyMed records loaded yet. The Exact Ingredients tab can search and inspect individual SPL labels.")

    st.write("### 🌍 Regulatory-source map")
    st.dataframe(pd.DataFrame([
        ["US generic / therapeutic equivalence", "FDA Orange Book", "Product, dosage form, route, application, reference status, TE code"],
        ["US approval history", "Drugs@FDA / openFDA", "Applications, products, submissions and approval-related data"],
        ["US current labeling", "DailyMed / NLM", "Structured product labeling submitted by companies and currently in use"],
        ["EU product information", "EMA ePI", "Electronic product information including SmPC, package leaflet and labelling where available"],
    ], columns=["Purpose", "Source", "What PharmaLens can use"]), use_container_width=True, hide_index=True)

    st.caption("Source map: FDA Orange Book, openFDA, DailyMed/NLM and EMA ePI. Product-level regulatory status remains jurisdiction-, strength-, dosage-form- and route-specific.")

with tabs[5]:
    process=PROCESS_DATA[get_process_type(selected_form)]
    st.subheader(f"High-level manufacturing risk map: {selected_form}")
    st.write("### Process stages")
    for n,step in enumerate(process["process"],1):st.write(f"{n}. {step}")
    st.write("### Possible defects")
    st.dataframe(pd.DataFrame([{"Possible defect":d,"Investigation focus":"Review material attributes, equipment status, process parameters, IPC data, deviation history, cleaning and batch documentation."} for d in process["defects"]]),use_container_width=True,hide_index=True)
    st.write("### Typical quality checks")
    st.dataframe(pd.DataFrame({"Quality check":process["tests"],"Purpose":["Confirm dosage-form performance and consistency"]*len(process["tests"])}),use_container_width=True,hide_index=True)
    st.warning("Actual production must follow approved specifications, validated processes, GMP requirements, authorized SOPs and approved batch records.")

with tabs[6]:
    st.subheader("Formulation-development checklist")
    for item in ["Confirm API identity, assay, polymorph or salt form where relevant","Evaluate particle size, flow, density, moisture and compatibility","Select dosage form based on therapeutic need and product performance","Screen excipient compatibility and concentration ranges","Define critical quality attributes","Identify critical material attributes and process parameters","Perform stability and packaging studies","Define in-process controls and acceptance criteria","Investigate defects through documented root-cause analysis","Use CAPA and continued process verification after validation"]:
        st.checkbox(item,value=False)

st.divider()
st.caption("PharmaLens 100 | Educational research dashboard | Always verify current product labels, publications and regulatory requirements.")
