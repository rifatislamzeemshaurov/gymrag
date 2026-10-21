"""Generate the sample supplement catalog PDFs in ../data/.

Every brand, product, price and spec in these guides is fictional demo data.
The guides are deliberately laid out like real retailer PDFs (cover page,
editor's notes, numbered listings, spec tables, review paragraphs, page
footers) so the ingestion notebook has realistic, messy input to clean up.

Replace the PDFs in ../data/ with a real catalog and re-run
rag_pipeline.ipynb; this script is only needed to rebuild the demo data.

    uv run --project ../backend --with reportlab python build_sample_catalog.py
"""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    KeepTogether,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# (brand, product, brand overview, quantity / servings, price, {spec label: value}, review)
WHEY = [
    ("IronForge Labs", "Titan Whey Isolate", "Engineered for lean muscle, built for serious lifters.", "2 lbs / 30 Servings", "$54.99",
     {"Protein per Serving": "25g", "Protein Source": "Whey Isolate"},
     "Ultra-clean isolate that mixes with a single shake. Low lactose, almost zero sugar, and a light vanilla taste that works in oats or coffee."),
    ("Apex Athletics", "Daily Whey Blend", "Massive gains, massive scoops.", "5 lbs / 74 Servings", "$69.99",
     {"Protein per Serving": "24g", "Protein Source": "Whey Isolate & Concentrate Blend"},
     "A dependable everyday blend with excellent value per serving. Mixes great, tastes like victory. 10/10 would chug."),
    ("Titan Nutrition", "Hydro Isolate Pro", "Fast-digesting protein for elite recovery.", "3.5 lbs / 40 Servings", "$79.99",
     {"Protein per Serving": "30g", "Protein Source": "Hydrolyzed Whey Isolate"},
     "Pre-digested hydrolyzed isolate that hits the bloodstream fast. The highest protein per scoop in this guide, priced accordingly."),
    ("PureLift", "Grass-Fed Whey", "One ingredient. Nothing to hide.", "2 lbs / 30 Servings", "$49.99",
     {"Protein per Serving": "25g", "Protein Source": "Grass-Fed Whey Concentrate"},
     "Unflavored, unsweetened concentrate from grass-fed cows. Blends into smoothies without changing the taste. Ideal for clean-label fans."),
    ("Vanta Sport", "Micropure Whey Isolate", "Clean protein for clean bulks.", "2 lbs / 28 Servings", "$42.99",
     {"Protein per Serving": "25g", "Protein Source": "Micro-Filtered Whey Isolate"},
     "Cross-flow micro-filtered isolate with a smooth chocolate flavor. Light on the stomach and one of the best-priced isolates listed."),
    ("NorthPeak Nutrition", "Alpine Whey", "Protein from the mountains to your shaker.", "2 lbs / 27 Servings", "$39.99",
     {"Protein per Serving": "22g", "Protein Source": "Whey Concentrate"},
     "A budget-friendly concentrate with a creamy texture. Slightly lower protein per scoop, but hard to beat on price."),
    ("Kinetic Labs", "Superhuman Protein", "Built for athletes who refuse to plateau.", "2 lbs / 25 Servings", "$50.19",
     {"Protein per Serving": "25g", "Protein Source": "Whey Isolate & Concentrate Blend"},
     "Dessert-style flavors with digestive enzymes added. Mixes thick and tastes indulgent without blowing your macros."),
    ("Olympus Supplements", "Lean Isolate", "Massive gains, massive scoops.", "2 lbs / 26 Servings", "$44.76",
     {"Protein per Serving": "25g", "Protein Source": "Whey Isolate"},
     "A no-nonsense isolate with clean macros. Mixes great, tastes like victory. 10/10 would chug."),
    ("Redline Performance", "Redline Whey 100", "Fuel for those who live at the limit.", "5 lbs / 70 Servings", "$64.99",
     {"Protein per Serving": "23g", "Protein Source": "Whey Concentrate & Isolate"},
     "Great bulk value for big households and team kitchens. Cookies and cream flavor is a crowd favorite."),
    ("Summit Fuel", "Summit Clear Whey", "Protein that drinks like juice.", "1.1 lbs / 20 Servings", "$36.99",
     {"Protein per Serving": "20g", "Protein Source": "Clear Whey Isolate"},
     "A refreshing, juice-like clear isolate for hot days. Light and fruity rather than milky. Lower protein per serving than classic shakes."),
    ("CoreStrong", "Core Isolate Zero", "Zero sugar. Zero compromise.", "4 lbs / 55 Servings", "$74.99",
     {"Protein per Serving": "27g", "Protein Source": "Whey Isolate"},
     "Zero sugar, zero fat isolate with 27g of protein per scoop. Excellent choice for cutting phases."),
    ("Primal Edge", "Primal Native Whey", "Undenatured protein, the way nature built it.", "2 lbs / 30 Servings", "$58.50",
     {"Protein per Serving": "26g", "Protein Source": "Native Whey Isolate"},
     "Cold-processed native whey with a naturally high leucine content. Premium price, premium quality."),
    ("Velocity Nutrition", "Velocity Whey Plus", "Speed up your recovery.", "2 lbs / 32 Servings", "$34.99",
     {"Protein per Serving": "21g", "Protein Source": "Whey Concentrate"},
     "The cheapest whey in this guide. Decent mixability and a classic chocolate flavor for lifters on a tight budget."),
    ("Atlas Performance", "Atlas Mass Whey", "Carry more weight.", "6 lbs / 16 Servings", "$59.99",
     {"Protein per Serving": "50g", "Protein Source": "Whey Concentrate with Oat Carbs"},
     "A high-calorie mass gainer style shake with 50g protein and 250g carbs per double serving. Built for hard gainers who struggle to eat enough."),
    ("Halo Wellness", "Halo Plant Protein", "Plant power for every body.", "2 lbs / 30 Servings", "$46.99",
     {"Protein per Serving": "24g", "Protein Source": "Pea & Brown Rice Protein (Dairy-Free)"},
     "A dairy-free alternative for lactose-intolerant lifters. Earthy but smooth; best blended with fruit."),
    ("BlackRidge Labs", "BlackRidge Isolate Elite", "Elite protein for elite athletes.", "2 lbs / 30 Servings", "$52.00",
     {"Protein per Serving": "25g", "Protein Source": "Whey Isolate"},
     "Third-party tested for banned substances, making it a safe pick for competitive athletes. Mild vanilla flavor."),
    ("Evolve Sports", "Evolve Whey Hybrid", "Evolve your physique.", "3 lbs / 40 Servings", "$47.49",
     {"Protein per Serving": "24g", "Protein Source": "Whey Isolate & Casein Blend"},
     "A blend of fast whey and slow casein for steady amino acid release. A versatile choice for both post-workout and before bed."),
    ("Granite Nutrition", "Granite Night Casein", "Recover while you sleep.", "2 lbs / 26 Servings", "$45.99",
     {"Protein per Serving": "24g", "Protein Source": "Micellar Casein"},
     "Slow-digesting micellar casein for overnight recovery. Thick, pudding-like texture when mixed with less water."),
    ("Nova Strength", "Nova Whey Isolate", "Next-generation protein.", "2 lbs / 30 Servings", "$40.20",
     {"Protein per Serving": "25g", "Protein Source": "Whey Isolate"},
     "A great-value isolate with 25g protein per scoop. Mixes great, tastes like victory. 10/10 would chug."),
    ("Zenith Labs", "Zenith Collagen Whey", "Strength from the inside out.", "2 lbs / 28 Servings", "$55.99",
     {"Protein per Serving": "25g", "Protein Source": "Whey Isolate with Collagen Peptides"},
     "Combines whey isolate with collagen peptides for joint and tendon support. Popular with older lifters and runners."),
]

CREATINE = [
    ("IronForge Labs", "Forge Creatine Monohydrate", "Trusted source for daily ATP regeneration and muscle fullness.", "300g / 60 Servings", "$24.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Micronized Monohydrate"},
     "Unflavored micronized monohydrate that dissolves cleanly. The gold-standard form at a sensible price."),
    ("Apex Athletics", "Apex Pure Creatine", "Strength you can measure.", "500g / 100 Servings", "$29.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate"},
     "The best value per serving in this guide. Plain monohydrate, no fillers, no flavoring."),
    ("Titan Nutrition", "Titan Creatine HCl", "Less bloat, more power.", "120 Capsules / 120 Servings", "$24.45",
     {"Creatine per Serving": "750mg", "Creatine Form": "Creatine HCl"},
     "A concentrated HCl capsule that needs a smaller dose. A good option for lifters who feel bloated on monohydrate."),
    ("PureLift", "PureLift Creatine Gummies", "Creatine you actually look forward to.", "90 Gummies / 30 Servings", "$34.99",
     {"Creatine per Serving": "4.5g", "Creatine Form": "Monohydrate Gummies"},
     "Three tasty gummies per serving. Convenient for travel, but the most expensive way to get your daily creatine."),
    ("Vanta Sport", "Vanta Creatine Caps", "Grab, swallow, lift.", "180 Capsules / 36 Servings", "$22.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate Capsules"},
     "Five capsules deliver a full 5g dose. Ideal for people who dislike the gritty texture of powder."),
    ("NorthPeak Nutrition", "NorthPeak Micronized Creatine", "Pure performance, sourced responsibly.", "400g / 80 Servings", "$27.50",
     {"Creatine per Serving": "5g", "Creatine Form": "Micronized Monohydrate"},
     "Ultra-fine powder that mixes into any drink without clumping. Made in a certified facility."),
    ("Kinetic Labs", "Kinetic Buffered Creatine", "pH-buffered for a smoother experience.", "120 Capsules / 40 Servings", "$31.99",
     {"Creatine per Serving": "3g", "Creatine Form": "Buffered Creatine"},
     "A buffered form marketed for better stomach tolerance. Lower dose per serving than monohydrate."),
    ("Olympus Supplements", "Olympus Creatine Plus Electrolytes", "Hydrate. Saturate. Dominate.", "345g / 30 Servings", "$32.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate with Electrolytes"},
     "Flavored creatine with sodium, potassium and magnesium added. Great for training in hot weather."),
    ("Redline Performance", "Redline Creatine Matrix", "Five forms. One scoop.", "300g / 50 Servings", "$36.99",
     {"Creatine per Serving": "6g", "Creatine Form": "Multi-Form Blend (Monohydrate, HCl, Malate)"},
     "A multi-form blend with the highest dose per serving in this guide. Fruit punch flavor."),
    ("Summit Fuel", "Summit Creatine Magnesium Chelate", "Gentle strength for sensitive stomachs.", "120 Capsules / 60 Servings", "$28.99",
     {"Creatine per Serving": "2.5g", "Creatine Form": "Creatine Magnesium Chelate"},
     "Creatine bound to magnesium for gentle absorption. Lower dose, but a favorite of endurance athletes."),
    ("CoreStrong", "CoreStrong Creatine 1000", "Big tub. Small price.", "1000g / 200 Servings", "$44.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate"},
     "A kilogram tub that lasts more than six months. Best long-term value for committed lifters."),
    ("Primal Edge", "Primal Creatine Unflavored", "Nothing added. Nothing missing.", "250g / 50 Servings", "$19.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate"},
     "The cheapest tub in this guide. Simple, effective, and unflavored."),
    ("Velocity Nutrition", "Velocity Creatine Chews", "Power on the go.", "60 Chews / 30 Servings", "$29.99",
     {"Creatine per Serving": "3g", "Creatine Form": "Monohydrate Chews"},
     "Soft chews for lifters who hate mixing powders. Tasty but lower dose per serving."),
    ("Atlas Performance", "Atlas Creatine Load", "Saturate fast. Lift heavy.", "500g / 100 Servings", "$26.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Micronized Monohydrate"},
     "Includes a printed 7-day loading guide. Mixes clear in water."),
    ("Halo Wellness", "Halo Vegan Creatine", "Plant-friendly strength.", "300g / 60 Servings", "$25.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Vegan Monohydrate"},
     "Certified vegan and allergen-free. Especially useful for plant-based athletes who get little creatine from food."),
    ("BlackRidge Labs", "BlackRidge Creatine Tested", "Third-party tested for competitive athletes.", "300g / 60 Servings", "$29.95",
     {"Creatine per Serving": "5g", "Creatine Form": "Micronized Monohydrate"},
     "Batch-tested for banned substances. The safest creatine choice for drug-tested competitors."),
    ("Evolve Sports", "Evolve Creatine HCl Powder", "Small scoop. Full power.", "120g / 80 Servings", "$27.99",
     {"Creatine per Serving": "1.5g", "Creatine Form": "Creatine HCl"},
     "A highly soluble HCl powder with a tiny scoop. Mixes fully clear even in cold water."),
    ("Granite Nutrition", "Granite Creatine + Beta-Alanine", "Strength meets endurance.", "360g / 40 Servings", "$34.50",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate with Beta-Alanine"},
     "Combines 5g creatine with 3.2g beta-alanine for strength and muscular endurance. Expect a mild tingle."),
    ("Nova Strength", "Nova Creatine Monohydrate", "Science-backed strength.", "300g / 60 Servings", "$21.99",
     {"Creatine per Serving": "5g", "Creatine Form": "Monohydrate"},
     "An affordable everyday creatine with no frills and great results."),
    ("Zenith Labs", "Zenith Creatine Ethyl Ester", "An alternative form for the curious.", "120 Capsules / 30 Servings", "$26.49",
     {"Creatine per Serving": "2g", "Creatine Form": "Creatine Ethyl Ester"},
     "An alternative form with a capsule format. Research generally favors monohydrate, so this is a niche pick."),
]

PRE_WORKOUT = [
    ("IronForge Labs", "Forge Ignite Pre", "Engineered for high-intensity training, tunnel vision, and explosive strength.", "30 Servings", "$39.99",
     {"Caffeine per Serving": "300mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "Hits fast and hard. Excellent mixability and flavor profile. Provides sustained energy without a devastating crash afterward."),
    ("Apex Athletics", "Apex Overload Pre", "Engineered for high-intensity training, tunnel vision, and explosive strength.", "40 Servings", "$52.16",
     {"Caffeine per Serving": "400mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "The strongest stimulant pre-workout in this guide. Intense focus and a big tingle. A staple for intense training blocks, not for beginners."),
    ("Titan Nutrition", "Titan Pump Stim-Free", "All pump, no jitters.", "30 Servings", "$44.99",
     {"Caffeine per Serving": "0mg", "L-Citrulline (Pump)": "8g", "Beta-Alanine (Endurance)": "3.2g"},
     "Completely stimulant-free with the highest citrulline dose listed. Ideal for evening sessions or caffeine-sensitive lifters."),
    ("PureLift", "PureLift Clean Pre", "Clean energy from natural caffeine.", "20 Servings", "$34.50",
     {"Caffeine per Serving": "150mg", "L-Citrulline (Pump)": "4g", "Beta-Alanine (Endurance)": "1.6g"},
     "Natural caffeine from green tea and coffee beans. A gentle option for beginners who want focus without jitters."),
    ("Vanta Sport", "Vanta Nitro Surge", "Unleash the surge.", "30 Servings", "$37.99",
     {"Caffeine per Serving": "250mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "2g"},
     "A balanced, well-rounded formula. Smooth energy, solid pumps, and a sour candy flavor."),
    ("NorthPeak Nutrition", "NorthPeak Summit Pre", "Climb higher every session.", "25 Servings", "$32.99",
     {"Caffeine per Serving": "200mg", "L-Citrulline (Pump)": "5g", "Beta-Alanine (Endurance)": "2g"},
     "A mid-strength pre with a clean finish. Good for morning lifters who already drink coffee."),
    ("Kinetic Labs", "Kinetic Ascent Pre", "Rise to the challenge.", "40 Servings", "$50.02",
     {"Caffeine per Serving": "250mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "Clinically dosed and transparently labeled. Hits fast and hard with excellent mixability."),
    ("Olympus Supplements", "Olympus Thunder", "Power worthy of the gods.", "30 Servings", "$46.99",
     {"Caffeine per Serving": "350mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "A high-stimulant formula for experienced users. Expect strong focus and a long-lasting energy curve."),
    ("Redline Performance", "Redline Overdrive", "Push past the red line.", "20 Servings", "$44.50",
     {"Caffeine per Serving": "350mg", "L-Citrulline (Pump)": "4g", "Beta-Alanine (Endurance)": "3.2g"},
     "Intense energy with a heavy tingle. Engineered for high-intensity training, tunnel vision, and explosive strength."),
    ("Summit Fuel", "Summit Endurance Pre", "Go longer. Go stronger.", "30 Servings", "$36.50",
     {"Caffeine per Serving": "200mg", "L-Citrulline (Pump)": "5g", "Beta-Alanine (Endurance)": "3.2g"},
     "Designed for long sessions, CrossFit and running. Includes electrolytes to keep you hydrated."),
    ("CoreStrong", "CoreStrong Pre Zero", "Zero sugar. All focus.", "30 Servings", "$34.99",
     {"Caffeine per Serving": "200mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "2.5g"},
     "Sugar-free and calorie-free. A reliable middle-of-the-road pre for daily training."),
    ("Primal Edge", "Primal Rage Pre", "Unlock primal intensity.", "25 Servings", "$42.99",
     {"Caffeine per Serving": "325mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "A hard-hitting formula with added nootropics for focus. Best reserved for heavy leg days."),
    ("Velocity Nutrition", "Velocity Budget Pre", "Big energy. Small price.", "30 Servings", "$24.99",
     {"Caffeine per Serving": "200mg", "L-Citrulline (Pump)": "3g", "Beta-Alanine (Endurance)": "1.6g"},
     "The cheapest pre-workout in this guide. Underdosed on pump ingredients, but the energy is real."),
    ("Atlas Performance", "Atlas Pump Matrix", "Maximum blood flow.", "20 Servings", "$41.99",
     {"Caffeine per Serving": "100mg", "L-Citrulline (Pump)": "8g", "Beta-Alanine (Endurance)": "2g"},
     "A pump-focused formula with only a light caffeine dose. Great sleeve-splitting pumps for arm day."),
    ("Halo Wellness", "Halo Calm Focus", "Focus without the frenzy.", "30 Servings", "$38.99",
     {"Caffeine per Serving": "100mg", "L-Citrulline (Pump)": "4g", "Beta-Alanine (Endurance)": "0g"},
     "Low caffeine paired with L-theanine for calm, clear focus. No beta-alanine, so no tingle."),
    ("BlackRidge Labs", "BlackRidge Tested Pre", "Competition-safe energy.", "30 Servings", "$43.99",
     {"Caffeine per Serving": "200mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "Third-party tested for banned substances. The go-to pre for drug-tested athletes."),
    ("Evolve Sports", "Evolve Ignite Pre-Workout", "Engineered for high-intensity training, tunnel vision, and explosive strength.", "30 Servings", "$55.18",
     {"Caffeine per Serving": "200mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "3.2g"},
     "Hits fast and hard. Excellent mixability and flavor profile. Provides sustained energy without a devastating crash afterward."),
    ("Granite Nutrition", "Granite Stim-Free Pump", "Pump without the buzz.", "40 Servings", "$39.50",
     {"Caffeine per Serving": "0mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "1.6g"},
     "A second stimulant-free option at a lower price. Good for stacking with your own coffee."),
    ("Nova Strength", "Nova Pre-Workout Complex", "Every ingredient fully dosed.", "20 Servings", "$34.42",
     {"Caffeine per Serving": "150mg", "L-Citrulline (Pump)": "6g", "Beta-Alanine (Endurance)": "2g"},
     "A well-rounded complex with moderate caffeine. A sensible first pre-workout."),
    ("Zenith Labs", "Zenith Focus Pre", "Laser focus for every rep.", "30 Servings", "$44.50",
     {"Caffeine per Serving": "350mg", "L-Citrulline (Pump)": "4g", "Beta-Alanine (Endurance)": "3.2g"},
     "A focus-first formula with a strong nootropic blend. Hits fast and hard, then tapers off smoothly."),
]

POST_WORKOUT = [
    ("IronForge Labs", "Forge Recovery EAA", "Rebuild faster between sessions.", "30 Servings", "$36.99",
     {"Amino Acids per Serving": "10g EAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 200mg, Potassium 100mg"},
     "Full-spectrum essential amino acids with glutamine. Noticeably reduces soreness during high-volume training blocks."),
    ("Apex Athletics", "Apex BCAA 2:1:1", "The classic recovery formula.", "60 Servings", "$29.99",
     {"Amino Acids per Serving": "7g BCAA", "Glutamine per Serving": "0g", "Electrolytes": "None"},
     "A budget-friendly BCAA powder in the classic 2:1:1 ratio. Refreshing flavors, but no glutamine or electrolytes."),
    ("Titan Nutrition", "Titan Post-Workout Matrix", "Everything your muscles need after the last rep.", "20 Servings", "$49.99",
     {"Amino Acids per Serving": "15g EAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 300mg, Potassium 200mg, Magnesium 50mg"},
     "The most complete recovery formula in this guide. Includes fast carbs for glycogen refill. Pricier, but nothing is missing."),
    ("PureLift", "PureLift Tart Cherry Recovery", "Natural recovery, powered by fruit.", "30 Servings", "$34.99",
     {"Amino Acids per Serving": "5g EAA", "Glutamine per Serving": "2g", "Electrolytes": "Potassium 150mg"},
     "Tart cherry extract for soreness plus a light amino dose. A gentle, natural option for runners."),
    ("Vanta Sport", "Vanta Hydro Recover", "Hydrate and recover in one scoop.", "30 Servings", "$32.50",
     {"Amino Acids per Serving": "8g EAA", "Glutamine per Serving": "3g", "Electrolytes": "Sodium 400mg, Potassium 200mg, Magnesium 60mg"},
     "Recovery plus the highest electrolyte dose listed. Excellent for summer training and heavy sweaters."),
    ("NorthPeak Nutrition", "NorthPeak Glutamine Pure", "Pure glutamine, nothing else.", "100 Servings", "$24.99",
     {"Amino Acids per Serving": "0g", "Glutamine per Serving": "5g", "Electrolytes": "None"},
     "Unflavored L-glutamine that can be added to any shake. Best value for glutamine on its own."),
    ("Kinetic Labs", "Kinetic Night Repair", "Recover while you sleep.", "30 Servings", "$39.99",
     {"Amino Acids per Serving": "6g EAA", "Glutamine per Serving": "3g", "Electrolytes": "Magnesium 200mg"},
     "A caffeine-free evening recovery drink with magnesium and glycine to support sleep quality."),
    ("Olympus Supplements", "Olympus Ambrosia Recovery", "Recovery fit for the gods.", "25 Servings", "$42.99",
     {"Amino Acids per Serving": "12g EAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 250mg, Potassium 150mg"},
     "A premium EAA formula with a smooth tropical flavor. Great for back-to-back training days."),
    ("Redline Performance", "Redline Rebuild", "Rebuild. Refuel. Repeat.", "30 Servings", "$37.99",
     {"Amino Acids per Serving": "10g BCAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 150mg"},
     "High-dose BCAAs with glutamine. Popular with lifters training twice a day."),
    ("Summit Fuel", "Summit Endurance Recovery", "Built for long-distance athletes.", "20 Servings", "$38.50",
     {"Amino Acids per Serving": "8g EAA", "Glutamine per Serving": "2g", "Electrolytes": "Sodium 350mg, Potassium 200mg"},
     "A carb and protein recovery mix designed for runners and cyclists after long sessions."),
    ("CoreStrong", "CoreStrong EAA Zero", "Zero sugar recovery.", "30 Servings", "$31.99",
     {"Amino Acids per Serving": "9g EAA", "Glutamine per Serving": "0g", "Electrolytes": "Sodium 100mg"},
     "Sugar-free EAAs that can be sipped during training or after. A clean everyday option."),
    ("Primal Edge", "Primal Recovery Fuel", "Feed the machine.", "25 Servings", "$44.99",
     {"Amino Acids per Serving": "10g EAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 200mg, Potassium 200mg"},
     "A dense recovery formula with added creatine for strength athletes. Thick berry flavor."),
    ("Velocity Nutrition", "Velocity BCAA Budget", "Recovery for every wallet.", "50 Servings", "$22.99",
     {"Amino Acids per Serving": "5g BCAA", "Glutamine per Serving": "1g", "Electrolytes": "None"},
     "The cheapest recovery product in this guide. A light dose, but a solid starting point."),
    ("Atlas Performance", "Atlas Recovery Shake", "Carry the load, recover the load.", "20 Servings", "$46.99",
     {"Amino Acids per Serving": "20g Protein + 5g EAA", "Glutamine per Serving": "3g", "Electrolytes": "Sodium 200mg"},
     "A complete post-workout shake with whey, fast carbs and EAAs. Basically a meal replacement for hard gainers."),
    ("Halo Wellness", "Halo Vegan Recovery", "Plant-powered repair.", "30 Servings", "$35.99",
     {"Amino Acids per Serving": "8g Plant EAA", "Glutamine per Serving": "2g", "Electrolytes": "Potassium 100mg"},
     "Fermented plant-based amino acids for vegan athletes. Mild citrus flavor."),
    ("BlackRidge Labs", "BlackRidge Tested Recovery", "Competition-safe recovery.", "30 Servings", "$40.99",
     {"Amino Acids per Serving": "10g EAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 200mg, Potassium 100mg"},
     "Third-party tested for banned substances. Recommended for drug-tested competitors."),
    ("Evolve Sports", "Evolve Joint & Recovery", "Recover muscles and joints together.", "30 Servings", "$43.50",
     {"Amino Acids per Serving": "6g EAA", "Glutamine per Serving": "3g", "Electrolytes": "None"},
     "Adds collagen, turmeric and glucosamine for joint comfort. Great for lifters with achy knees and elbows."),
    ("Granite Nutrition", "Granite Mag-Recovery", "Relax. Repair. Rebuild.", "60 Servings", "$27.99",
     {"Amino Acids per Serving": "0g", "Glutamine per Serving": "0g", "Electrolytes": "Magnesium 300mg, Zinc 15mg"},
     "A ZMA-style magnesium and zinc formula taken before bed. Supports sleep, which is where recovery really happens."),
    ("Nova Strength", "Nova EAA Hydration", "Train harder, recover smarter.", "30 Servings", "$33.99",
     {"Amino Acids per Serving": "9g EAA", "Glutamine per Serving": "2g", "Electrolytes": "Sodium 250mg, Potassium 150mg"},
     "A great all-rounder that blends EAAs and hydration. Easy to drink in large shakers."),
    ("Zenith Labs", "Zenith Recovery Pro", "Professional-grade recovery.", "30 Servings", "$47.99",
     {"Amino Acids per Serving": "12g EAA", "Glutamine per Serving": "5g", "Electrolytes": "Sodium 300mg, Potassium 150mg, Magnesium 50mg"},
     "A premium recovery stack with HMB added for muscle preservation during cutting phases."),
]

MULTIVITAMIN = [
    ("IronForge Labs", "Forge Athlete Multi", "Micronutrient support for hard training.", "60 Tablets / 30 Servings", "$24.99",
     {"Serving Size": "2 Tablets", "Key Nutrients": "Vitamin D3 2000 IU, Zinc 15mg, Magnesium 200mg, B-Complex", "Best For": "Active Adults"},
     "A complete daily multi tuned for athletes, with higher magnesium and zinc than standard formulas."),
    ("Apex Athletics", "Apex Men's Daily", "Daily foundation for active men.", "90 Tablets / 90 Servings", "$19.99",
     {"Serving Size": "1 Tablet", "Key Nutrients": "Vitamin D3 1000 IU, Zinc 11mg, Selenium 55mcg, Lycopene", "Best For": "Men"},
     "A one-a-day men's formula at a great price. Easy to take and well tolerated."),
    ("Titan Nutrition", "Titan Women's Multi", "Daily foundation for active women.", "60 Capsules / 60 Servings", "$22.99",
     {"Serving Size": "1 Capsule", "Key Nutrients": "Iron 18mg, Folate 400mcg, Vitamin D3 1000 IU, Calcium 200mg", "Best For": "Women"},
     "Includes iron and folate for active women. Gentle on the stomach when taken with food."),
    ("PureLift", "PureLift Whole Food Multi", "Vitamins from real food.", "120 Tablets / 30 Servings", "$34.99",
     {"Serving Size": "4 Tablets", "Key Nutrients": "Fruit & Vegetable Blend, Vitamin C 250mg, Vitamin K2, Probiotics", "Best For": "Clean-Label Fans"},
     "Whole-food sourced vitamins with probiotics. Four tablets a day is a lot, but the ingredient list is spotless."),
    ("Vanta Sport", "Vanta Daily Essentials", "Cover the basics.", "100 Tablets / 100 Servings", "$14.99",
     {"Serving Size": "1 Tablet", "Key Nutrients": "Vitamin A, C, D3, E, B-Complex, Zinc 8mg", "Best For": "Everyday Use"},
     "The cheapest multivitamin in this guide. Covers the basics without extras."),
    ("NorthPeak Nutrition", "NorthPeak Vegan Multi", "Plant-based, complete.", "60 Capsules / 60 Servings", "$26.99",
     {"Serving Size": "1 Capsule", "Key Nutrients": "Vitamin B12 500mcg, Vitamin D3 (Lichen) 1000 IU, Iron 10mg, Iodine", "Best For": "Vegans"},
     "Certified vegan with high B12 and plant-sourced D3. Fills the gaps common in plant-based diets."),
    ("Kinetic Labs", "Kinetic Performance Multi", "Built for output.", "120 Capsules / 30 Servings", "$39.99",
     {"Serving Size": "4 Capsules", "Key Nutrients": "Vitamin D3 5000 IU, Magnesium 300mg, Zinc 30mg, CoQ10, Antioxidant Blend", "Best For": "Competitive Athletes"},
     "A high-potency formula for heavy training loads. Split the dose between breakfast and dinner."),
    ("Olympus Supplements", "Olympus Immune Multi", "Stay in the gym, not in bed.", "60 Tablets / 30 Servings", "$27.99",
     {"Serving Size": "2 Tablets", "Key Nutrients": "Vitamin C 1000mg, Zinc 25mg, Vitamin D3 2000 IU, Elderberry", "Best For": "Immune Support"},
     "Extra vitamin C, zinc and elderberry for the cold season. Helps you stay consistent with training."),
    ("Redline Performance", "Redline Multi + Omega", "Two essentials in one pack.", "30 Packs / 30 Servings", "$44.99",
     {"Serving Size": "1 Pack (3 Tablets + 2 Softgels)", "Key Nutrients": "Full Multivitamin, Omega-3 1000mg EPA/DHA, Vitamin D3 2000 IU", "Best For": "Convenience"},
     "Daily packs that combine a multi and fish oil. Very convenient, though the most expensive per serving."),
    ("Summit Fuel", "Summit 50+ Multi", "Strong at every age.", "90 Tablets / 90 Servings", "$23.99",
     {"Serving Size": "1 Tablet", "Key Nutrients": "Vitamin B12 100mcg, Vitamin D3 2000 IU, Calcium 300mg, Lutein", "Best For": "Adults 50+"},
     "Designed for older lifters with extra B12, vitamin D and calcium for bone health."),
    ("CoreStrong", "CoreStrong Gummy Multi", "Vitamins that taste like candy.", "120 Gummies / 60 Servings", "$21.99",
     {"Serving Size": "2 Gummies", "Key Nutrients": "Vitamin A, C, D3, E, B6, B12, Zinc 5mg", "Best For": "People Who Hate Pills"},
     "Great-tasting gummies with modest doses. Contains a little sugar, and no iron."),
    ("Primal Edge", "Primal Testo Multi", "Support for male vitality.", "90 Capsules / 30 Servings", "$36.99",
     {"Serving Size": "3 Capsules", "Key Nutrients": "Zinc 30mg, Vitamin D3 5000 IU, Magnesium 400mg, Boron 6mg", "Best For": "Men Over 30"},
     "High zinc, magnesium and vitamin D for men. Not a hormone, just well-dosed micronutrients."),
    ("Velocity Nutrition", "Velocity Teen Athlete Multi", "Foundations for young athletes.", "60 Chewables / 60 Servings", "$18.99",
     {"Serving Size": "1 Chewable", "Key Nutrients": "Calcium 250mg, Vitamin D3 600 IU, Iron 8mg, B-Complex", "Best For": "Teen Athletes (14-18)"},
     "A chewable multi with age-appropriate doses for teenage athletes. Orange flavor."),
    ("Atlas Performance", "Atlas Mass Multi", "Micronutrients for big appetites.", "180 Tablets / 60 Servings", "$29.99",
     {"Serving Size": "3 Tablets", "Key Nutrients": "B-Complex High Potency, Chromium 200mcg, Digestive Enzymes", "Best For": "Bulking"},
     "Digestive enzymes help with high-calorie diets. Pairs well with mass gainers."),
    ("Halo Wellness", "Halo Women's 40+ Multi", "Balanced support for women 40 and over.", "60 Tablets / 60 Servings", "$25.99",
     {"Serving Size": "1 Tablet", "Key Nutrients": "Calcium 400mg, Vitamin D3 2000 IU, Magnesium 150mg, Vitamin K2", "Best For": "Women 40+"},
     "Iron-free with bone-support nutrients for women over 40. Small, easy-to-swallow tablets."),
    ("BlackRidge Labs", "BlackRidge Tested Multi", "Competition-safe daily vitamins.", "60 Tablets / 30 Servings", "$28.99",
     {"Serving Size": "2 Tablets", "Key Nutrients": "Vitamin D3 2000 IU, Zinc 15mg, Iron 9mg, B-Complex", "Best For": "Drug-Tested Athletes"},
     "Third-party tested for banned substances. A safe daily multi for competitive athletes."),
    ("Evolve Sports", "Evolve Sleep & Recover Multi", "Night-time micronutrients.", "60 Capsules / 30 Servings", "$31.99",
     {"Serving Size": "2 Capsules", "Key Nutrients": "Magnesium Glycinate 300mg, Zinc 15mg, Vitamin B6, Melatonin 1mg", "Best For": "Poor Sleepers"},
     "Taken before bed to support sleep quality and recovery. Contains a low dose of melatonin."),
    ("Granite Nutrition", "Granite Iron-Free Multi", "Complete without the iron.", "90 Tablets / 90 Servings", "$20.99",
     {"Serving Size": "1 Tablet", "Key Nutrients": "Vitamin D3 1000 IU, Zinc 11mg, B-Complex, Vitamin K2", "Best For": "Men & Post-Menopausal Women"},
     "An iron-free daily multi for people who don't need extra iron. Simple, effective and affordable."),
    ("Nova Strength", "Nova Liquid Multi", "Fast-absorbing liquid vitamins.", "450ml / 30 Servings", "$29.50",
     {"Serving Size": "15ml", "Key Nutrients": "Vitamin B12 250mcg, Vitamin D3 1000 IU, Trace Minerals, Aloe Vera", "Best For": "Trouble Swallowing Pills"},
     "A liquid multi with a pleasant berry flavor. Good for people who can't swallow tablets."),
    ("Zenith Labs", "Zenith Endurance Multi", "Built for the long run.", "60 Capsules / 30 Servings", "$33.99",
     {"Serving Size": "2 Capsules", "Key Nutrients": "Iron 18mg, Vitamin B12 500mcg, Sodium & Potassium, Vitamin C 500mg", "Best For": "Runners & Cyclists"},
     "Iron and B12 support for endurance athletes, with electrolytes to replace what's lost in sweat."),
]

GUIDES = [
    ("Whey_Protein_Guide.pdf", "THE ULTIMATE WHEY PROTEIN GUIDE", "Isolates, Blends and 20 Top Proteins Reviewed", WHEY, "#b45309"),
    ("Creatine_Ultimate_Guide.pdf", "THE ULTIMATE CREATINE GUIDE", "Strength, Saturation and 20 Top Creatines Reviewed", CREATINE, "#1d4ed8"),
    ("PreWorkout_Ultimate_Guide.pdf", "THE ULTIMATE PRE-WORKOUT DIRECTORY", "Focus, Pump, and 20 Top Supplements Reviewed", PRE_WORKOUT, "#c2410c"),
    ("PostWorkout_Recovery_Guide.pdf", "THE POST-WORKOUT RECOVERY HANDBOOK", "EAAs, Glutamine and 20 Recovery Formulas Reviewed", POST_WORKOUT, "#047857"),
    ("Multivitamin_Ultimate_Guide.pdf", "THE ULTIMATE MULTIVITAMIN GUIDE", "Daily Foundations and 20 Top Multis Reviewed", MULTIVITAMIN, "#7c3aed"),
]

EDITOR_NOTE = (
    "Prices are listed in USD and were checked at the time of writing; they change often. "
    "Serving counts follow the manufacturer's label. Read every label carefully, start with "
    "a half dose when trying a new stimulant, and speak to a qualified professional if you "
    "have a medical condition. Products are listed in no particular order."
)


def _footer(title: str):
    def draw(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(18 * mm, 10 * mm, f"{title.title()} - Sample Edition 2026")
        canvas.drawRightString(A4[0] - 18 * mm, 10 * mm, f"Page {doc.page}")
        canvas.restoreState()

    return draw


def build_guide(filename: str, title: str, subtitle: str, products, accent: str) -> Path:
    styles = getSampleStyleSheet()
    accent_color = colors.HexColor(accent)
    cover = ParagraphStyle("cover", parent=styles["Title"], fontSize=30, leading=36, textColor=accent_color, alignment=TA_CENTER)
    cover_sub = ParagraphStyle("coversub", parent=styles["Italic"], fontSize=14, alignment=TA_CENTER, textColor=colors.HexColor("#334155"))
    heading = ParagraphStyle("heading", parent=styles["Heading2"], textColor=colors.HexColor("#1e3a8a"), spaceBefore=10)
    review_head = ParagraphStyle("reviewhead", parent=styles["Heading4"], textColor=accent_color)
    body = ParagraphStyle("body", parent=styles["BodyText"], fontSize=10, leading=14)

    story = [
        Spacer(1, 70 * mm),
        Paragraph(title, cover),
        Spacer(1, 8 * mm),
        Paragraph(subtitle, cover_sub),
        PageBreak(),
        Paragraph("Editor's Note", styles["Heading1"]),
        Paragraph(EDITOR_NOTE, body),
        Spacer(1, 6 * mm),
    ]

    for i, (brand, name, overview, qty, price, specs, review) in enumerate(products, start=1):
        rows = [["Quantity / Servings", qty], ["Price", price]] + [[k, v] for k, v in specs.items()]
        table = Table(rows, colWidths=[60 * mm, 95 * mm])
        table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cbd5e1")),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#f1f5f9")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(KeepTogether([
            Paragraph(f"{i:02d}. {brand} - {name}", heading),
            Paragraph(f"<b>Brand Overview:</b> {overview}", body),
            Spacer(1, 2 * mm),
            table,
            Paragraph("Review &amp; Efficacy", review_head),
            Paragraph(review, body),
            Spacer(1, 4 * mm),
        ]))

    out = DATA_DIR / filename
    doc = SimpleDocTemplate(str(out), pagesize=A4, title=title.title(), author="GymRAG Sample Data",
                            leftMargin=18 * mm, rightMargin=18 * mm, topMargin=18 * mm, bottomMargin=18 * mm)
    doc.build(story, onFirstPage=_footer(title), onLaterPages=_footer(title))
    return out


def main() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    for filename, title, subtitle, products, accent in GUIDES:
        path = build_guide(filename, title, subtitle, products, accent)
        print(f"{path.name}: {len(products)} products")


if __name__ == "__main__":
    main()
