# Evaluation: rule pass vs T5-small (ADR 0005)

## A. ASLG-PC12 held-out test split

Model `google-t5/t5-small`, 3.0 epochs, lr 0.0003, batch 32, 78940 training rows, 1020 s on NVIDIA GeForce RTX 4080 Laptop GPU. Split seed 20260903, sizes {'test': 4385, 'val': 4385, 'train': 78940}.

| Metric | Score |
|---|---|
| BLEU | 93.7 |
| chrF | 97.1 |

Caveat, stated up front: ASLG-PC12 glosses were rule-generated from parliamentary text, so this split measures how well T5 learned those rules, not how well it glosses news.

Samples (text → reference gloss → T5):

- our support for ratification this week should make clear three points .
  - ref: `X-WE SUPPORT FOR RATIFICATION THIS WEEK SHOULD MAKE DESC-CLEAR THREE POINT .`
  - t5: `X-WE SUPPORT FOR RATIFICATION THIS WEEK SHOULD MAKE DESC-CLEAR THREE POINT.`
- i agree that we need greater trust and understanding between the eu and russia .
  - ref: `X-I AGREE THAT X-WE NEED DESC-GREATER TRUST AND UNDERSTANDING BETWEEN EU AND RUSSIUM .`
  - t5: `X-I AGREE THAT X-WE NEED DESC-GREATER TRUST AND UNDERSTANDING BETWEEN EU AND RUSSIUM.`
- it does not belong here and , as such , does not belong in these guidelines .
  - ref: `X-IT DO DESC-NOT BELONG DESC-HERE AND , AS DESC-SUCH , DO DESC-NOT BELONG IN SE GUIDELINE .`
  - t5: `X-IT DO DESC-NOT BELONG DESC-HERE AND, AS DESC-SUCH, DO DESC-NOT BELONG IN SE GUIDELINE.`
- membership of committees and delegations see minutes
  - ref: `MEMBERSHIP COMMITTEE AND DELEGATION SEE MINUTE`
  - t5: `MEMBERSHIP COMMITTEE AND DELEGATION SEE MINUTE`
- now for two points .
  - ref: `DESC-NOW FOR TWO POINT .`
  - t5: `DESC-NOW FOR TWO POINT.`
- this is a very real risk I can envisage .
  - ref: `THIS BE DESC-VERY DESC-REAL RISK X-I CAN ENVISAGE .`
  - t5: `THIS BE DESC-VERY DESC-REAL RISK X-I CAN ENVISAGE.`

## B. Curated news items and a forecast, both engines through the same lexicon

| Item | Engine | Content tokens | Coverage | Fingerspelled | Names as text | Not available | Signing s | Build ms |
|---|---|---|---|---|---|---|---|---|
| samoa-oil-spill | rules | 47 | 68% | 28% | 2 | 0 | 150 | 1 |
| samoa-oil-spill | t5 | 48 | 60% | 40% | 0 | 0 | 172 | 334 |
| california-fire-warning | rules | 50 | 90% | 10% | 0 | 0 | 110 | 1 |
| california-fire-warning | t5 | 39 | 77% | 23% | 0 | 0 | 125 | 151 |
| sichuan-landslide | rules | 40 | 85% | 15% | 0 | 0 | 118 | 0 |
| sichuan-landslide | t5 | 40 | 60% | 38% | 0 | 1 | 149 | 155 |
| pope-infection | rules | 43 | 81% | 16% | 0 | 1 | 139 | 0 |
| pope-infection | t5 | 47 | 66% | 30% | 0 | 2 | 168 | 188 |
| canada-new-pm | rules | 75 | 81% | 16% | 2 | 0 | 217 | 1 |
| canada-new-pm | t5 | 61 | 67% | 33% | 0 | 0 | 244 | 256 |
| astronauts-return | rules | 49 | 76% | 20% | 2 | 0 | 145 | 1 |
| astronauts-return | t5 | 56 | 68% | 27% | 2 | 1 | 172 | 240 |
| nws-forecast-sample | rules | 34 | 91% | 9% | 0 | 0 | 80 | 0 |
| nws-forecast-sample | t5 | 40 | 80% | 18% | 0 | 1 | 108 | 163 |
| **All** | **rules** | 338 | **81%** | **17%** | 6 | 1 | 959 | |
| **All** | **t5** | 331 | **68%** | **30%** | 2 | 5 | 1137 | |

Legend for the gloss lines below: `[word:fi]` fingerspelled, `[word:na]` name shown as text, `[word:no]` not available.

## C. Side-by-side glosses for the manual review

### samoa-oil-spill

> Samoa's acting prime minister said late Sunday an oil spill from a grounded New Zealand navy ship that sank and caught fire off the coast of Samoa is, quote, "highly probable." Officials in the Pacific island nation are conducting an environmental impact assessment in the area where the ship sank on Sunday morning. New Zealand's chief of Navy said all 75 people on board were taken to safety on life rafts.

- **rules**: `NIGHT SUNDAY [samoa:fi] [acting:fi] LEADERb SAYstr OIL SPILL [grounded:fi] NEW [zealand:fi] SHIP SINK AND FIREstr [off:fi] BEACHb [samoa:na] [quote:fi] HIGH [probable:fi] SUNDAY MORNING OFFICIAL OCEAN ISLAND COUNTRY [conducting:fi] ENVIRONMENT [impact:fi] [assessment:fi] AREA WHERE SHIP SINK NEW [zealand:na] LEADERb ARMY SAYstr ALL 75 PEOPLEdis [board:fi] SAFE [life:fi] [rafts:fi]`
- **t5**: `[smooa:fi] NIGHT SUNDAY [act:fi] [desc-prime:fi] LEADERb SAYstr OIL SPILL [blast:fi] NEW [zealand:fi] [colleague:fi] SHIP SINK AND [catch:fi] FIREstr [off:fi] BEACHb [smooa:fi] OFFICIAL SUNDAY MORNING OCEAN ISLAND COUNTRY [conduct:fi] ENVIRONMENT [impact:fi] [assessment:fi] AREA WHERE SHIP [stank:fi] NEW [zealand:fi] [chair:fi] [bless:fi] SAYstr ALL 75 PEOPLEdis [board:fi] TAKE SAFE [life:fi] [rapport:fi]`

### california-fire-warning

> Southern Californians are again bracing for gusty winds and a heightened risk of wildfires less than two weeks after the start of deadly blazes that have killed at least 27 people and destroyed thousands of homes. The U.S. National Weather Service has issued a red flag warning signaling increased fire danger for Los Angeles on Monday and Tuesday due to low humidity and warm, dry Santa Ana winds.

- **rules**: `WEEK SOUTH CALIFORNIA AGAIN PREPARE WIND WIND AND INCREASE RISK DANGER FIREstr LESS TWO AFTER START KILLix FIREstr KILLix [least:fi] 27 PEOPLEdis AND DESTROY THOUSAND HOUSE AMERICA MONDAY TUESDAY COUNTRY WEATHER SERVICE ISSUE WARN WARN SIGNAL INCREASE RISK FIREstr DANGER [los:fi] [angeles:fi] AND DUE TO LOW HUMID AND WARM DRY [santa:fi] [ana:fi] WIND`
- **t5**: `[desc-sourn:fi] WEEK [calestinian:fi] AGAIN [brac:fi] [desc-gurgy:fi] WIND AND [desc-greaten:fi] DANGER FIREstr LESS TWO AFTER START DANGER AMERICA COUNTRY WEST MONDAY TUESDAY SERVICE ISSUE [red:fi] FLAG WARN SIGNAL INCREASE FIREstr DANGER [la:fi] [angel:fi] AND DUE TO LOW [feilure:fi] AND WARM LETTER-D`

### sichuan-landslide

> Chinese rescuers are searching for some 30 people after a landslide in southwestern Sichuan province buried 10 houses. The Ministry of Emergency Management deployed hundreds of rescuers, including firefighters, following the landslide Saturday in the Junlian county. State broadcaster CCTV said two people were pulled out alive and about 200 others evacuated.

- **rules**: `CHINA RESCUE SEARCH MANY 30 PEOPLEdis AFTER LANDSLIDE [southwestern:fi] [sichuan:fi] AREA BURY 10 HOUSE SATURDAY OFFICIAL EMERGENCY MANAGEx [deployed:fi] HUNDRED RESCUE WITH FIREFIGHTERb AFTER LANDSLIDE [junlian:fi] CITYtwist GOVERNMENT [broadcaster:fi] [cctv:fi] SAYstr TWO PEOPLEdis RESCUE ALIVE AND NEAR 200 PEOPLEdis ESCAPE`
- **t5**: `CHINA [rescuer:fi] SEARCH MANY 30 PEOPLEdis AFTER LANDSLIDE [desc-westernwenn:no] AREA [green:fi] 10 HOUSE OFFICIAL EMERGENCY MANAGEx [deploy:fi] HUNDRED [rescuer:fi] [include:fi] [femaler:fi] [follow:fi] LANDSLIDE [sateday:fi] [junelian:fi] COUNTRY GOVERNMENT [distributor:fi] [ctctv:fi] SAYstr TWO PEOPLEdis [pull:fi] [out:fi] ALIVE AND NEAR 200 [desc-or:fi] [available:fi]`

### pope-infection

> Vatican authorities said Monday that Pope Francis has a complex infection in his respiratory system and will require more targeted drug treatment. Officials said the 88-year-old pope is suffering from a polymicrobial respiratory tract infection but gave few details. Experts say that's not uncommon in older people with prior medical problems and should be treatable with the right antibiotics.

- **rules**: `MONDAY POPE OFFICIAL SAYstr POPE [francis:fi] [complex:fi] SICK [respiratory:fi] [system:fi] AND NEED MORE [targeted:fi] MEDICINE MEDICINE YEAR OFFICIAL SAYstr 88 POPE SICK [polymicrobial:no] [respiratory:fi] [tract:fi] SICK BUT GIVEo FEW DETAIL DOCTOR SAYstr NO COMMON OLD PEOPLEdis BEFORE HEALTH PROBLEM AND MEDICINE RIGHT MEDICINE`
- **t5**: `[vitacan:fi] MONDAY OFFICIAL SAYstr [ppe:fi] [france:fi] [complex:fi] [instance:fi] [desc-radical:fi] [system:fi] AND NEED MORE [target:fi] MEDICINE MEDICINE OFFICIAL YEAR SAYstr 88 OLD [pop:fi] SICK [desc-polymicrobial:no] [desc-radical:fi] [train:fi] [instance:fi] BUT GIVEo FEW DETAIL DOCTOR SAYstr NO COMMON OLD PEOPLEdis WITH BEFORE HEALTH PROBLEM AND [should:fi] [desc-traditable:no] WITH RIGHT [anticipant:fi]`

### canada-new-pm

> Former central banker Mark Carney will become Canada's next prime minister after the governing Liberal Party elected him its leader on Sunday as the country deals with President Trump's trade war and annexation threat and a federal election looms. The 59-year-old Carey replaces Prime Minister Justin Trudeau, who announced his resignation in January but remains prime minister until his successor is sworn in. Carney navigated crises when he was the head of the Bank of Canada, and in 2013 he became the first noncitizen to run the Bank of England since it was founded in 1694. Trudeau's popularity had declined as food and housing prices rose and immigration surged.

- **rules**: `LAST NEXT SUNDAY [central:fi] BANK [mark:fi] [carney:fi] BECOME CANADA LEADERb AFTER GOVERNMENT [liberal:fi] PARTY ELECTION LEADERb COUNTRY DEAL PRESIDENT [trump:fi] TRADE WAR AND [annexation:fi] THREAT AND GOVERNMENT ELECTION [looms:fi] YEAR 59 [carey:fi] REPLACE LEADERb [justin:fi] [trudeau:fi] WHO SAYstr RESIGN [january:fi] BUT CONTINUE LEADERb BEFORE REPLACE [sworn:fi] [carney:na] MANAGEx PROBLEM WHEN LEADERb BANK CANADA AND 2013 BECOME FIRST CITIZEN MANAGEx BANK ENGLAND SINCE ESTABLISH 1694 [trudeau:na] POPULAR DECREASEb EAT AND HOUSE PRICE INCREASE AND IMMIGRATION INCREASE`
- **t5**: `LAST NEXT [desc-central:fi] BANK [mark:fi] [quarey:fi] BECOME CANADA [desc-prime:fi] LEADERb AFTER [govern:fi] [desc-liberal:fi] PARTY ELECTION 59 YEAR OLD [carey:fi] REPLACE [desc-prime:fi] LEADERb [justin:fi] [trudau:fi] WHO SAYstr [remission:fi] [january:fi] BUT CONTINUE [desc-prime:fi] LEADERb BEFORE [carino:fi] [brown:fi] PROBLEM WHEN LEADERb BANK CANADA AND 2013 BECOME FIRST [noncizen:fi] MANAGEx BANK ENGLAND SINCE [find:fi] [trudau:fi] [potentiality:fi] DECREASEb EAT AND HOUSE PRICE INCREASE AND IMMIGRATION [short:fi]`

### astronauts-return

> Two astronauts who have been living on the International Space Station since June of last year are about to get their ride back to Earth. SpaceX launched four astronauts from Kennedy Space Center in Florida on Friday night to the space station. Butch Wilmore and Suni Williams have been on the space station since their Boeing Starliner capsule suffered a malfunction and returned to Earth without them. Wilmore and Williams are expected back on Earth next week.

- **rules**: `LAST YEAR TWO ASTRONAUT WHO LIVE WORLD STATION SINCE [june:fi] NEAR GET GO-BACK EARTH FRIDAY NIGHT [spacex:fi] ROCKET FOUR ASTRONAUT [kennedy:fi] SPACE [center:fi] FLORIDA STATION [butch:fi] [wilmore:fi] AND [suni:fi] [williams:fi] STATION SINCE [boeing:fi] [starliner:fi] CAPSULE SICK BROKEN AND GO-BACK EARTH WITHOUT NEXT WEEK [wilmore:na] AND [williams:na] EXPECT GO-BACK EARTH`
- **t5**: `TWO LAST YEAR [approacher:fi] WHO LIVE WORLD SPACE STATION SINCE [june:fi] NEAR GET LETTER-Y [root:fi] GO-BACK EARTH [spacex:fi] FRIDAY NIGHT ROCKET FOUR [abstructor:fi] [keedy:fi] SPACE [center:fi] [flida:fi] SPACE STATION [butch:fi] [wilmore:fi] AND [sunus:fi] [william:fi] SPACE STATION SINCE LETTER-Y [bee:fi] [starliner:fi] [capture:fi] SICK [disfortability:no] AND GO-BACK EARTH WITHOUT LETTER-Y [wilmore:na] NEXT WEEK AND [william:na] EXPECT GO-BACK EARTH`

### nws-forecast-sample

> This Afternoon. Sunny, with a high near 97. Heat index values as high as 105. Tonight. Mostly clear, with a low around 75. Saturday. A slight chance of showers and thunderstorms between 2pm and 4pm. Partly cloudy, with a low around 72. Chance of precipitation is 30%.

- **rules**: `AFTERNOON SUNNY HIGH NEAR 97 HOT [values:fi] HIGH 105 TONIGHT CLEAR LOW NEAR 75 SATURDAY SLIGHT CHANCE RAIN AND THUNDERSTORM BETWEEN 2 [pm:fi] AND 4 [pm:fi] CLOUDY LOW NEAR 72 CHANCE PRECIPITATION 30 PERCENT`
- **t5**: `AFTERNOON SUNDAY WITH HIGH NEAR 97 HOT SIGNAL [value:fi] HIGH 105 TONIGHT MOSTLY CLEAR WITH LOW NEAR 75 SATURDAY SMALL CHANCE [during:fi] AND [horror:fi] BETWEEN 2 [pm:fi] AND 4 [pm:fi] [desc-partly:fi] [desc-lowy:fi] WITH LOW NEAR 72 CHANCE [primelisation:no] 30 PERCENT`

## D. Decision (2026-09-04)

**The rule pass stays the default.** On the seven items T5 covers 68% of content tokens against 81% for the rules, fingerspells 30% against 17%, and refuses 5 tokens against 1. The manual review (Part C) shows why: T5 reproduces its training corpus's vocabulary and habits, not the news. It invents spellings for words it never saw ("smooa" for Samoa, "vitacan" for Vatican, "flida" for Florida), replaces unknown news words with corpus words ("horror" for thunderstorms, "colleague" for navy, "capture" for capsule), and drops the time-fronting the rules do deliberately. Its ASLG-PC12 scores (BLEU 93.7, chrF 97.1) are high precisely because that corpus's glosses were generated by rules from parliamentary English; the model learned those rules well and they do not transfer.

What T5 does well: sentence-level word order and function-word handling are fluent, and it runs torch-free at 32–71 ms per sentence with 86 MB of resident memory (spike 3). What would change the decision: fine-tuning on a news-domain English→gloss corpus written by signers, which does not exist as an open dataset today.

For the report this is the honest deep-learning finding: a small seq2seq model fits an in-domain synthetic corpus almost perfectly and still loses to 150 lines of rules on real news, because the failure that matters is vocabulary, not grammar. The toggle stays in the app so an examiner can see both.

Reproduce: `python training/train_t5_gloss.py --epochs 3` (any GPU; ~17 min on an RTX 4080), `python training/export_ct2.py --best <out>/best --out models/t5_gloss_ct2`, `python scripts/evaluate_gloss.py`.
