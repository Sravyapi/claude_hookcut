export interface NichePage {
  slug: string;
  niche: string;
  intro: string;
  hookTypes: { type: string; description: string }[];
  failureReason: string;
  metaTitle: string;
  metaDescription: string;
}

export const nichePages: NichePage[] = [
  {
    slug: "finance",
    niche: "Finance",
    intro:
      "Finance creators sit in one of the most competitive niches on YouTube Shorts. Viewers scroll past vague money tips constantly — the only clips that stop the scroll are the ones that create immediate tension: a shocking statistic, a counterintuitive claim, or a painfully relatable problem. HookCut identifies these moments automatically in your finance videos.",
    hookTypes: [
      {
        type: "Shock Statistic",
        description: "A number so surprising it demands attention — '73% of people making $100K still live paycheck to paycheck.'",
      },
      {
        type: "Contrarian Claim",
        description: "Challenge conventional financial wisdom — 'Paying off your mortgage early is actually a bad idea.'",
      },
      {
        type: "Pain Escalation",
        description: "Name a financial fear and amplify it — 'Most people don't realize how much inflation is eating their savings.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the payoff — 'The one fee your bank doesn't want you to know about.'",
      },
      {
        type: "Proof Opening",
        description: "Lead with results — 'I paid off $80,000 in debt in 26 months. Here's the exact method.'",
      },
    ],
    failureReason:
      "Finance videos fail as Shorts when creators open with disclaimers, hedge every claim, or bury the insight at the end. The algorithm punishes slow openers — if your first 2 seconds are 'Today I want to talk about investing,' viewers are already gone. Finance creators also tend to summarize before revealing, which kills tension before it builds.",
    metaTitle: "YouTube Hook Ideas for Finance Creators | HookCut",
    metaDescription:
      "Find the scroll-stopping moments in your finance videos. HookCut identifies shock statistics, contrarian claims, and pain escalation hooks in any finance YouTube video.",
  },
  {
    slug: "fitness",
    niche: "Fitness",
    intro:
      "Fitness Shorts live or die on transformation tension and contrarian training advice. The fitness niche is saturated — every creator shows workouts. The ones that go viral open with a claim that challenges what viewers believe about exercise, diet, or body composition. HookCut surfaces these hook moments in your fitness content automatically.",
    hookTypes: [
      {
        type: "Myth Busting",
        description: "Directly challenge popular fitness beliefs — 'You don't need to do cardio to lose fat.'",
      },
      {
        type: "Transformation Proof",
        description: "Lead with a visual result — 'I did 100 push-ups a day for 30 days. Here's what actually happened.'",
      },
      {
        type: "Shock Statistic",
        description: "Use data to reframe effort — 'Most people overtrain and it's killing their progress.'",
      },
      {
        type: "Pain Escalation",
        description: "Name the common struggle — 'If you've been going to the gym for a year and still don't see results...'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the technique — 'The one exercise that changed my physique faster than anything else.'",
      },
    ],
    failureReason:
      "Fitness videos fail as Shorts when they open with workout demonstrations instead of hooks. A clip of someone doing a squat has zero context and zero tension. Fitness creators also lose viewers by leading with motivation speech rather than actionable insights — 'You can do it!' is not a hook.",
    metaTitle: "YouTube Hook Ideas for Fitness Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your fitness videos. HookCut identifies myth-busting claims, transformation proof, and curiosity gap hooks in any fitness YouTube content.",
  },
  {
    slug: "cooking",
    niche: "Cooking",
    intro:
      "Cooking Shorts have a built-in advantage: visual results. But most cooking clips fail because they start with mise en place instead of the payoff. The hooks that stop scrollers in the cooking niche are the ones that reveal something unexpected — a technique nobody knew, an ingredient that changes everything, or a result that seems impossible. HookCut finds these moments in your cooking videos.",
    hookTypes: [
      {
        type: "Technique Reveal",
        description: "Lead with a surprising method — 'This one mistake is why your pasta never tastes like a restaurant.'",
      },
      {
        type: "Ingredient Surprise",
        description: "Challenge assumptions — 'The secret ingredient professional chefs add that nobody talks about.'",
      },
      {
        type: "Result First",
        description: "Show the outcome before the process — lead with the finished dish at its most dramatic.",
      },
      {
        type: "Contrarian Claim",
        description: "Challenge cooking dogma — 'You should never wash chicken. Here's why.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create tension around a technique — 'I tried the Gordon Ramsay scrambled egg method. The result surprised me.'",
      },
    ],
    failureReason:
      "Cooking videos fail as Shorts when creators start with ingredient lists, lengthy prep montages, or generic voiceovers. The hook is never 'today I'm making pasta' — it's the unexpected twist in the recipe, the chef's secret, or the result that defies expectations.",
    metaTitle: "YouTube Hook Ideas for Cooking Creators | HookCut",
    metaDescription:
      "Find the most viral moments in your cooking videos. HookCut identifies technique reveals, ingredient surprises, and result-first hooks in any cooking YouTube content.",
  },
  {
    slug: "tech",
    niche: "Tech",
    intro:
      "Tech Shorts succeed when they make complex tools feel accessible or expose something that changes how viewers work. The best tech hooks aren't product reviews — they're moments that reframe a tool, reveal a hidden feature, or challenge a widely-held assumption about software, AI, or productivity. HookCut identifies these moments in your tech content.",
    hookTypes: [
      {
        type: "Hidden Feature Reveal",
        description: "Expose something most users don't know — 'This ChatGPT feature has been there since launch and almost nobody uses it.'",
      },
      {
        type: "Workflow Transformation",
        description: "Show before/after of a tool change — 'This one Chrome extension saves me 2 hours every day.'",
      },
      {
        type: "Contrarian Claim",
        description: "Challenge tech orthodoxy — 'The most expensive laptop isn't always the fastest for creative work.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue about a tool — 'I tested every AI writing tool for 30 days. One was significantly better.'",
      },
      {
        type: "Shock Statistic",
        description: "Use data to reframe tech adoption — 'The average developer wastes 3 hours a day on tasks AI could do instantly.'",
      },
    ],
    failureReason:
      "Tech videos fail as Shorts when they lead with unboxing, spec lists, or technical jargon. Viewers don't stop scrolling for benchmark numbers — they stop for the moment that changes how they think about a tool they already use.",
    metaTitle: "YouTube Hook Ideas for Tech Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your tech videos. HookCut identifies hidden feature reveals, workflow transformations, and contrarian tech claims in any tech YouTube content.",
  },
  {
    slug: "gaming",
    niche: "Gaming",
    intro:
      "Gaming Shorts compete in one of the fastest-moving categories on the platform. What works: moments of impossible skill, surprising game mechanics, and controversial takes on popular titles. What doesn't: generic gameplay without context. HookCut identifies the moments in your gaming content that are most likely to stop a scroll.",
    hookTypes: [
      {
        type: "Skill Proof",
        description: "Lead with a moment that seems impossible — open on the clutch play, not the match start.",
      },
      {
        type: "Contrarian Take",
        description: "Challenge the meta — 'Everyone plays this character wrong. Here's what actually works.'",
      },
      {
        type: "Game Mechanic Reveal",
        description: "Expose hidden interactions — 'This glitch has been in the game for 3 years and nobody noticed.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create tension around an outcome — 'I tried the worst-rated strategy in the game. Here's what happened.'",
      },
      {
        type: "Shock Statistic",
        description: "Use data from the game — 'Less than 0.1% of players have unlocked this achievement.'",
      },
    ],
    failureReason:
      "Gaming clips fail when they start with lobby screens, loading animations, or generic commentary. The hook moment is always a specific event within gameplay — not the context around it. Most gaming AI clippers surface the wrong segments because they optimize for coherent speech rather than peak gameplay moments.",
    metaTitle: "YouTube Hook Ideas for Gaming Creators | HookCut",
    metaDescription:
      "Find the most viral moments in your gaming videos. HookCut identifies skill proof, game mechanic reveals, and contrarian takes in any gaming YouTube content.",
  },
  {
    slug: "education",
    niche: "Education",
    intro:
      "Educational Shorts have a unique challenge: the content is genuinely valuable, but value alone doesn't stop scrollers. The hooks that work in education create immediate curiosity ('what I'm about to show you will change how you think about X') or challenge a widely-held misconception. HookCut finds these hook moments in your educational videos.",
    hookTypes: [
      {
        type: "Misconception Challenge",
        description: "Open by debunking a belief — 'Everything you learned about the Roman Empire is slightly wrong.'",
      },
      {
        type: "Counterintuitive Insight",
        description: "Surprise with a fact — 'The most effective study technique isn't what most students use.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create a question that demands an answer — 'Why did Einstein fail his university entrance exam?'",
      },
      {
        type: "Shock Statistic",
        description: "Use data to reframe a topic — 'Students who use this one method score 40% higher on average.'",
      },
      {
        type: "Proof Opening",
        description: "Lead with a result — 'I memorized an entire book using this method. Here's how.'",
      },
    ],
    failureReason:
      "Education videos fail as Shorts when they start with lesson context ('Today we're going to learn about...'), slow build-ups, or summary statements. The educational hook must create a question in the viewer's mind before delivering the answer — most educational Shorts start with the answer.",
    metaTitle: "YouTube Hook Ideas for Education Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your educational videos. HookCut identifies misconception challenges, counterintuitive insights, and curiosity gap hooks in any education YouTube content.",
  },
  {
    slug: "travel",
    niche: "Travel",
    intro:
      "Travel Shorts work when they make a destination feel either unrealistically beautiful or surprisingly accessible — or when they expose something that contradicts what travelers expect. The hooks that stop scrollers aren't scenic B-roll — they're specific claims about a place, a price, or an experience that challenge assumptions. HookCut identifies these moments in your travel content.",
    hookTypes: [
      {
        type: "Price Shock",
        description: "Challenge cost assumptions — 'I spent a full month in Bali for less than my NYC rent.'",
      },
      {
        type: "Hidden Gem Reveal",
        description: "Expose something tourists miss — 'This beach in Thailand has no tourists — and locals don't want you to know.'",
      },
      {
        type: "Expectation Subversion",
        description: "Contradict what viewers assume — 'Japan is not as expensive as everyone says. Here's the breakdown.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create mystery around a place — 'There's a village in Portugal where nobody locks their doors.'",
      },
      {
        type: "Contrarian Travel Advice",
        description: "Challenge popular itineraries — 'Skip the Eiffel Tower. Here's what Parisians actually do.'",
      },
    ],
    failureReason:
      "Travel clips fail when they lead with generic scenic shots, arrival montages, or uncontextualised food shots. Without a hook, B-roll is just background video. Viewers scroll past beautiful locations constantly — they stop for the surprising story or the unexpected practical information.",
    metaTitle: "YouTube Hook Ideas for Travel Creators | HookCut",
    metaDescription:
      "Find the most viral moments in your travel videos. HookCut identifies price shocks, hidden gem reveals, and expectation-subverting hooks in any travel YouTube content.",
  },
  {
    slug: "fashion",
    niche: "Fashion",
    intro:
      "Fashion Shorts that go viral aren't outfit reveals — they're moments that change how viewers think about style, budget, or their own wardrobe. The hooks that work in fashion create either desire (this outfit is stunning) or practical tension (this styling mistake you're probably making). HookCut identifies these moments in your fashion content.",
    hookTypes: [
      {
        type: "Styling Mistake",
        description: "Call out a common error — 'This one mistake makes every outfit look cheap, and most people make it.'",
      },
      {
        type: "Budget Reveal",
        description: "Create tension around price — 'This entire outfit cost less than a Starbucks coffee order.'",
      },
      {
        type: "Trend Contrarian",
        description: "Challenge current fashion — 'This trend is everywhere right now — and it's making people look shorter.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the transformation — 'I wore the same base outfit 5 ways. The results were very different.'",
      },
      {
        type: "Proof Opening",
        description: "Lead with a transformation result — before/after styling of the same person or garment.",
      },
    ],
    failureReason:
      "Fashion videos fail as Shorts when they open with slow outfit reveals, lengthy haul intros, or brand context ('this is from Zara and it's the new collection...'). Viewers stop for the tension — the mistake they're making, the price that surprises them, or the transformation they didn't expect.",
    metaTitle: "YouTube Hook Ideas for Fashion Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your fashion videos. HookCut identifies styling mistakes, budget reveals, and trend contrarian hooks in any fashion YouTube content.",
  },
  {
    slug: "beauty",
    niche: "Beauty",
    intro:
      "Beauty Shorts that stop scrollers are transformation-led or technique-revealing — they open with the result, not the process. The hooks that work in the beauty niche create either desire (this look is stunning) or practical tension (this product/technique you've been doing wrong). HookCut identifies these moments in your beauty content.",
    hookTypes: [
      {
        type: "Technique Myth Bust",
        description: "Challenge common practice — 'You've been applying concealer wrong. This is what makeup artists actually do.'",
      },
      {
        type: "Product Surprise",
        description: "Create unexpected product tension — 'The $8 drugstore product that outperformed my $80 serum.'",
      },
      {
        type: "Transformation Proof",
        description: "Lead with the result — open on the finished look, not the blank canvas.",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the technique — 'I tried a 1950s beauty routine for a week. Here's what actually worked.'",
      },
      {
        type: "Pain Escalation",
        description: "Name a common beauty struggle — 'If your foundation always looks cakey by noon, this is why.'",
      },
    ],
    failureReason:
      "Beauty videos fail as Shorts when they start with flat lays, product intros, or slow base application. Without the hook moment — the transformation, the technique reveal, or the surprising product comparison — beauty content is just process without payoff.",
    metaTitle: "YouTube Hook Ideas for Beauty Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your beauty videos. HookCut identifies technique reveals, product surprises, and transformation proof hooks in any beauty YouTube content.",
  },
  {
    slug: "lifestyle",
    niche: "Lifestyle",
    intro:
      "Lifestyle Shorts work when they make viewers either aspire to something or recognize themselves in a relatable moment. The hooks in lifestyle content are often more personal — a day in the life that reveals something surprising, a routine that contradicts expectations, or a lifestyle choice that challenges conventional wisdom. HookCut identifies these moments in your lifestyle videos.",
    hookTypes: [
      {
        type: "Lifestyle Reveal",
        description: "Open with a surprising fact about how you live — 'I haven't owned a car in 5 years. Here's what my life actually looks like.'",
      },
      {
        type: "Routine Contrarian",
        description: "Challenge common routines — 'I stopped making my bed every day. My productivity went up.'",
      },
      {
        type: "Pain Escalation",
        description: "Name a universal lifestyle struggle — 'If you feel exhausted by Sunday evening, this is probably why.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the lifestyle insight — 'I changed one morning habit and my entire day changed.'",
      },
      {
        type: "Proof Opening",
        description: "Lead with a result — 'I spent a year tracking my habits. This is what the data actually showed.'",
      },
    ],
    failureReason:
      "Lifestyle videos fail as Shorts when they open with generic morning routine footage, vague motivational statements, or unanchored B-roll. The hook must make a specific claim or reveal something specific — 'vibe' content without tension doesn't stop the scroll.",
    metaTitle: "YouTube Hook Ideas for Lifestyle Creators | HookCut",
    metaDescription:
      "Find the most viral moments in your lifestyle videos. HookCut identifies lifestyle reveals, routine contrarians, and curiosity gap hooks in any lifestyle YouTube content.",
  },
  {
    slug: "entrepreneurship",
    niche: "Entrepreneurship",
    intro:
      "Entrepreneurship Shorts that go viral challenge assumptions about business, money, or success. The hooks that work expose a mistake most founders are making, reveal a counterintuitive truth about building a business, or share a specific number or outcome that creates immediate tension. HookCut identifies these moments in your entrepreneurship content.",
    hookTypes: [
      {
        type: "Revenue Reveal",
        description: "Lead with a specific business outcome — 'This side project made ₹12 lakh in its first month.'",
      },
      {
        type: "Founder Mistake",
        description: "Expose a common error — 'The mistake most first-time founders make in their first 90 days.'",
      },
      {
        type: "Contrarian Business Advice",
        description: "Challenge startup orthodoxy — 'Stop trying to raise VC funding. Here's why bootstrapping wins.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue about a business model — 'This business makes $50,000/month with no employees.'",
      },
      {
        type: "Shock Statistic",
        description: "Use data to reframe entrepreneurship — '90% of startups fail. But almost none fail for the reason people think.'",
      },
    ],
    failureReason:
      "Entrepreneurship videos fail as Shorts when they open with motivation without specificity ('you can do it'), vague frameworks, or long context-setting. The entrepreneur hook is almost always specific — a number, a specific mistake, or a counterintuitive claim. Generality is the enemy of engagement in this niche.",
    metaTitle: "YouTube Hook Ideas for Entrepreneurship Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your entrepreneurship videos. HookCut identifies revenue reveals, founder mistakes, and contrarian business hooks in any entrepreneurship YouTube content.",
  },
  {
    slug: "real-estate",
    niche: "Real Estate",
    intro:
      "Real estate Shorts that stop scrollers challenge assumptions about property prices, investment returns, or market conditions. The best real estate hooks make something that feels inaccessible feel possible, or reveal something that contradicts what viewers have been told about the market. HookCut identifies these moments in your real estate content.",
    hookTypes: [
      {
        type: "Market Myth Bust",
        description: "Challenge what viewers believe — 'Everyone says it's a bad time to buy. Here's the data that says otherwise.'",
      },
      {
        type: "Price Shock",
        description: "Create tension around a number — 'This property made ₹40 lakh in appreciation in 2 years.'",
      },
      {
        type: "Investment Reveal",
        description: "Lead with a return — 'I bought a rental property with ₹0 down. Here's exactly how.'",
      },
      {
        type: "Contrarian Claim",
        description: "Challenge real estate wisdom — 'Renting is not throwing money away. Here's the math.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue — 'The neighborhood nobody is looking at that's outperforming prime areas.'",
      },
    ],
    failureReason:
      "Real estate videos fail as Shorts when they lead with property tours without context, generic market updates, or slow-building market analysis. The hook must create immediate financial relevance — a number, a counterintuitive market insight, or an investment reveal that challenges what viewers expect.",
    metaTitle: "YouTube Hook Ideas for Real Estate Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your real estate videos. HookCut identifies market myth busts, price shocks, and investment reveals in any real estate YouTube content.",
  },
  {
    slug: "cryptocurrency",
    niche: "Cryptocurrency",
    intro:
      "Crypto Shorts that perform well challenge predictions, reveal market patterns, or expose something counterintuitive about blockchain projects. The hooks in crypto content are often price-based or prediction-based — moments that create immediate stakes for anyone holding or considering crypto. HookCut identifies these moments in your crypto content.",
    hookTypes: [
      {
        type: "Price Prediction Tension",
        description: "Create stakes around a price target — 'Bitcoin at $100K is not the ceiling. Here's why.'",
      },
      {
        type: "Project Reveal",
        description: "Expose something surprising about a project — 'This altcoin has outperformed Bitcoin 3 years in a row.'",
      },
      {
        type: "Contrarian Market Take",
        description: "Challenge consensus — 'Everyone is buying the dip wrong. Here's what smart money actually does.'",
      },
      {
        type: "Shock Statistic",
        description: "Use data to reframe the market — '95% of crypto traders lose money. But not for the reason you think.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue — 'The on-chain signal that predicted the last 3 major moves.'",
      },
    ],
    failureReason:
      "Crypto videos fail as Shorts when they open with price charts without context, generic 'do your own research' disclaimers, or slow technical analysis setup. The crypto viewer is already engaged with the space — the hook must give them new information or a new frame, not context they already have.",
    metaTitle: "YouTube Hook Ideas for Cryptocurrency Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your crypto videos. HookCut identifies price prediction tension, contrarian market takes, and curiosity gap hooks in any cryptocurrency YouTube content.",
  },
  {
    slug: "health",
    niche: "Health",
    intro:
      "Health Shorts that go viral challenge what viewers believe about their own bodies, diet, or medical science. The hooks that work in the health niche create either urgency (something you're doing is harming you) or relief (something you worried about isn't as bad as you thought). HookCut identifies these moments in your health content.",
    hookTypes: [
      {
        type: "Health Myth Bust",
        description: "Challenge common health beliefs — 'Drinking 8 glasses of water a day is not based on real science.'",
      },
      {
        type: "Symptom Hook",
        description: "Create immediate personal relevance — 'If you feel tired all the time, this is probably why.'",
      },
      {
        type: "Research Reveal",
        description: "Lead with a study finding — 'New research shows this common supplement actually doesn't work.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the health insight — 'The one thing doctors wish patients knew about their own metabolism.'",
      },
      {
        type: "Shock Statistic",
        description: "Use health data to create urgency — '1 in 3 people have this deficiency and don't know it.'",
      },
    ],
    failureReason:
      "Health videos fail as Shorts when they open with excessive disclaimers, academic context, or vague wellness platitudes. The hook must make an immediate personal claim — something that makes the viewer think 'wait, is this about me?' — before anything else.",
    metaTitle: "YouTube Hook Ideas for Health Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your health videos. HookCut identifies health myth busts, symptom hooks, and research reveals in any health YouTube content.",
  },
  {
    slug: "relationships",
    niche: "Relationships",
    intro:
      "Relationship Shorts that perform well expose a behavior pattern, challenge an assumption, or name a specific dynamic that viewers immediately recognize. The hooks that work in relationships content make the viewer think 'this is exactly me' or 'I never thought about it that way.' HookCut identifies these moments in your relationship content.",
    hookTypes: [
      {
        type: "Pattern Naming",
        description: "Identify a behavior most people recognize — 'If your partner does this one thing, they're not being dismissive. They're overwhelmed.'",
      },
      {
        type: "Relationship Myth Bust",
        description: "Challenge popular relationship advice — 'Going to bed angry isn't always toxic. Here's what the research says.'",
      },
      {
        type: "Pain Escalation",
        description: "Name a universal relationship struggle — 'If you feel like you're always the one putting in effort...'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue around a dynamic — 'The reason most couples fight about the same things over and over.'",
      },
      {
        type: "Contrarian Advice",
        description: "Challenge conventional wisdom — 'Stop trying to communicate more. Here's what actually fixes relationship problems.'",
      },
    ],
    failureReason:
      "Relationship videos fail as Shorts when they open with generic advice ('communication is key'), slow scenario-building, or academic psychology framing. The hook must be immediately personal and specific — it should feel like the creator is describing the viewer's exact situation.",
    metaTitle: "YouTube Hook Ideas for Relationships Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your relationship videos. HookCut identifies pattern naming, relationship myth busts, and pain escalation hooks in any relationships YouTube content.",
  },
  {
    slug: "spirituality",
    niche: "Spirituality",
    intro:
      "Spirituality Shorts that go viral challenge mainstream assumptions, offer a reframe of common experiences, or reveal a practice that creates immediate curiosity. The hooks that work in spirituality create either a curiosity gap ('what is this practice?') or a recognition moment ('this explains something I've experienced'). HookCut identifies these moments in your spirituality content.",
    hookTypes: [
      {
        type: "Practice Reveal",
        description: "Open with an intriguing practice — 'I did a 10-day silent meditation retreat. This is what actually happened.'",
      },
      {
        type: "Reframe Hook",
        description: "Offer a new lens on a familiar concept — 'What most people call anxiety might actually be a spiritual signal.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue about a teaching — 'The Buddhist concept that changed how I experience every day.'",
      },
      {
        type: "Contrarian Spiritual Take",
        description: "Challenge mainstream spirituality — 'Toxic positivity is masquerading as spiritual growth.'",
      },
      {
        type: "Recognition Hook",
        description: "Name an experience viewers have had — 'Have you ever felt completely alone in a crowd? There's a name for that.'",
      },
    ],
    failureReason:
      "Spirituality videos fail as Shorts when they open with scripture quotes without context, vague motivation ('trust the universe'), or slow philosophical buildup. The hook must create immediate relevance — either a specific practice, a named experience, or a challenging claim that viewers haven't heard before.",
    metaTitle: "YouTube Hook Ideas for Spirituality Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your spirituality videos. HookCut identifies practice reveals, reframe hooks, and curiosity gap moments in any spirituality YouTube content.",
  },
  {
    slug: "comedy",
    niche: "Comedy",
    intro:
      "Comedy Shorts are uniquely challenging to clip because the hook and the punchline are often separated. The moments that stop scrollers in comedy are usually a setup with immediate tension, a surprising juxtaposition, or the first line of a bit that creates immediate anticipation. HookCut identifies the entry points — the moments where the bit begins — in your comedy content.",
    hookTypes: [
      {
        type: "Absurd Premise",
        description: "Open with a premise so ridiculous it demands resolution — 'I accidentally got a job at a company I applied to as a joke.'",
      },
      {
        type: "Relatable Tension",
        description: "Name a universal awkward situation — 'The panic when someone you know waves at you and you wave back but they were waving at someone behind you.'",
      },
      {
        type: "Contrast Hook",
        description: "Create unexpected juxtaposition — 'Being an adult is just telling people you're fine when you're absolutely not fine.'",
      },
      {
        type: "Storytelling Opener",
        description: "Lead with the most compelling line of the story — not the context, but the moment that hooks the listener.",
      },
      {
        type: "Observation Hook",
        description: "Open with an observation that's funny because it's true — a specific, relatable moment everyone has experienced.",
      },
    ],
    failureReason:
      "Comedy clips fail when they start with the setup context instead of the tension. The funniest moment in a comedy video is almost never the first minute — it's buried once the bit has built momentum. Generic AI clippers surface intros; HookCut surfaces the actual moment the bit gets interesting.",
    metaTitle: "YouTube Hook Ideas for Comedy Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your comedy videos. HookCut identifies absurd premises, relatable tension, and storytelling openers in any comedy YouTube content.",
  },
  {
    slug: "vlogs",
    niche: "Vlogs",
    intro:
      "Vlog Shorts that go viral aren't daily diary clips — they're the specific moments within vlogs where something surprising, emotional, or unexpected happens. The hooks that stop scrollers in vlogs are the moments of genuine reaction, the reveal of something that happened, or the specific insight buried in an ordinary day. HookCut identifies these moments in your vlog content.",
    hookTypes: [
      {
        type: "Event Hook",
        description: "Lead with a specific event — 'Something happened today that I wasn't expecting at all.'",
      },
      {
        type: "Reaction Moment",
        description: "Open on a moment of genuine emotion — surprise, delight, frustration — before context.",
      },
      {
        type: "Day Reveal",
        description: "Start with what was discovered — 'I found out today that [surprising fact about a place/person/situation].'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue about the vlog day — 'I said yes to everything for a day. This is what happened.'",
      },
      {
        type: "Behind the Scenes",
        description: "Open on something viewers never see — 'What filming a YouTube video actually looks like vs. what you see.'",
      },
    ],
    failureReason:
      "Vlog clips fail when they start with morning routines without a hook, generic 'hey guys welcome back,' or slow travel footage without context. The viral vlog moment is never the ordinary part of the day — it's the unexpected event, the genuine reaction, or the observation that stands out from the routine.",
    metaTitle: "YouTube Hook Ideas for Vlog Creators | HookCut",
    metaDescription:
      "Find the most viral moments in your vlogs. HookCut identifies event hooks, reaction moments, and day reveals in any vlog YouTube content.",
  },
  {
    slug: "music",
    niche: "Music",
    intro:
      "Music Shorts that go viral aren't just performances — they're the moments that challenge what viewers think about an artist, reveal an unexpected technique, or expose the story behind a song. The hooks in music content often blend performance with insight — the moment where the creator says or reveals something that changes how the viewer hears the music. HookCut identifies these moments in your music content.",
    hookTypes: [
      {
        type: "Technique Reveal",
        description: "Expose something surprising about music production — 'This is the sample that became one of the most famous songs ever.'",
      },
      {
        type: "Origin Story",
        description: "Lead with an unexpected story — 'This song was written in 15 minutes. It went on to win a Grammy.'",
      },
      {
        type: "Ear Training Hook",
        description: "Create a listening challenge — 'Most people can't hear this difference. Can you?'",
      },
      {
        type: "Contrarian Take",
        description: "Challenge music orthodoxy — 'The most overrated instrument in pop music, and what actually drives the groove.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the reveal — 'I rebuilt this famous song with nothing but free plugins. Here's the result.'",
      },
    ],
    failureReason:
      "Music videos fail as Shorts when they start with instrumental intros, tuning up, or vague song context. Without a hook — a specific insight, a challenge, or a reveal — music content becomes background audio that viewers scroll past. The hook must be verbal or visual, not just sonic.",
    metaTitle: "YouTube Hook Ideas for Music Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your music videos. HookCut identifies technique reveals, origin stories, and curiosity gap hooks in any music YouTube content.",
  },
  {
    slug: "sports",
    niche: "Sports",
    intro:
      "Sports Shorts that go viral aren't just highlight clips — they're the moments that explain something surprising about an athlete, challenge a popular sports narrative, or reveal a statistic that reframes a performance. The hooks in sports content combine the drama of competition with information that changes how viewers understand what they're watching. HookCut identifies these moments in your sports content.",
    hookTypes: [
      {
        type: "Skill Proof",
        description: "Lead with the most impressive moment — the statistical anomaly, the impossible play, the record-breaking performance.",
      },
      {
        type: "Sports Myth Bust",
        description: "Challenge conventional sports wisdom — 'The stats that prove [popular opinion about player/team] is wrong.'",
      },
      {
        type: "Behind the Play",
        description: "Explain what most viewers missed — 'Everyone talked about that goal. Nobody noticed what happened 3 seconds before it.'",
      },
      {
        type: "Shock Statistic",
        description: "Use data to reframe performance — 'This player's stat line is statistically the greatest season in the sport's history.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue around an athlete or team — 'The training method that made [athlete] 40% faster in one off-season.'",
      },
    ],
    failureReason:
      "Sports videos fail as Shorts when they lead with match context, team lineups, or pre-game analysis. The hook is always the specific insight or moment — the surprising stat, the tactical explanation, or the skill that viewers didn't fully appreciate. Context without tension is just preamble.",
    metaTitle: "YouTube Hook Ideas for Sports Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your sports videos. HookCut identifies skill proof, sports myth busts, and shock statistics in any sports YouTube content.",
  },
  {
    slug: "parenting",
    niche: "Parenting",
    intro:
      "Parenting Shorts that go viral name a specific parenting experience in a way that makes viewers feel immediately seen — or challenge a parenting belief that many parents secretly doubt. The hooks in parenting content are often relatable moments of recognition or surprising research that contradicts what parents have been told. HookCut identifies these moments in your parenting content.",
    hookTypes: [
      {
        type: "Recognition Hook",
        description: "Name a parenting moment everyone experiences — 'The look your toddler gives you right before they do something terrible.'",
      },
      {
        type: "Parenting Myth Bust",
        description: "Challenge popular parenting advice — 'Screen time research is not what parenting accounts tell you it is.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue around a parenting challenge — 'The one phrase that immediately stops a toddler tantrum.'",
      },
      {
        type: "Research Reveal",
        description: "Lead with a surprising study — 'Research shows children who do this one thing score higher on empathy tests.'",
      },
      {
        type: "Pain Escalation",
        description: "Name a universal parenting struggle — 'If bedtime is a battle in your house every night, this is probably why.'",
      },
    ],
    failureReason:
      "Parenting videos fail as Shorts when they open with generic parenting advice, slow scenario-building, or vague inspiration ('enjoy every moment'). The hook must create immediate recognition or surprise — parents scroll past advice they've heard before, but stop for the moment that names their exact experience.",
    metaTitle: "YouTube Hook Ideas for Parenting Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your parenting videos. HookCut identifies recognition hooks, parenting myth busts, and curiosity gap moments in any parenting YouTube content.",
  },
  {
    slug: "pets",
    niche: "Pets",
    intro:
      "Pet Shorts that perform well go beyond cute animal footage — they reveal something surprising about animal behavior, expose a common pet owner mistake, or share a health fact that creates immediate relevance for pet owners. The hooks in pet content combine the emotional pull of animals with information that changes how viewers care for or understand their pets. HookCut identifies these moments in your pet content.",
    hookTypes: [
      {
        type: "Behavior Reveal",
        description: "Explain a surprising animal behavior — 'This is why your dog stares at you when they're eating. It's not what you think.'",
      },
      {
        type: "Pet Owner Mistake",
        description: "Expose a common error — 'This food is in most people's kitchens and it's toxic to cats.'",
      },
      {
        type: "Training Insight",
        description: "Challenge training orthodoxy — 'The reason punishment training makes dogs worse, not better.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue about pet behavior — 'Why your cat brings you dead animals, according to animal behaviorists.'",
      },
      {
        type: "Health Reveal",
        description: "Lead with a health insight — 'Vets wish pet owners knew this before it becomes an emergency.'",
      },
    ],
    failureReason:
      "Pet videos fail as Shorts when they lead with generic cute footage without context, slow build-ups to the main point, or pet-owner diary content without a specific hook. The viral pet Short has a specific insight or behavior reveal — not just a loveable animal moment without information.",
    metaTitle: "YouTube Hook Ideas for Pet Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your pet videos. HookCut identifies behavior reveals, pet owner mistakes, and training insights in any pet YouTube content.",
  },
  {
    slug: "book-reviews",
    niche: "Book Reviews",
    intro:
      "Book review Shorts that go viral don't summarize books — they reveal the one insight from a book that changes how you think about something in your life. The hooks in book review content are either a surprising idea from the book, a counterintuitive piece of advice, or a concept that viewers immediately recognize applies to them. HookCut identifies these moments in your book review content.",
    hookTypes: [
      {
        type: "Key Insight Reveal",
        description: "Lead with the most surprising idea — 'One paragraph from this book changed how I think about time.'",
      },
      {
        type: "Book Myth Bust",
        description: "Challenge what viewers expect from a famous book — 'Atomic Habits is not actually about habits. It's about identity.'",
      },
      {
        type: "Applicability Hook",
        description: "Create immediate personal relevance — 'This book describes a pattern I had no words for until now.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the main idea — 'I read 100 books this year. One of them completely changed how I work.'",
      },
      {
        type: "Contrarian Take",
        description: "Challenge popular books — 'This bestseller gives advice that works — but only if you're already successful.'",
      },
    ],
    failureReason:
      "Book review videos fail as Shorts when they open with plot summaries, rating scales, or slow author context. The viewer who stops for a book review Short is already a reader — they want the idea, not the setup. Lead with the insight, not the book description.",
    metaTitle: "YouTube Hook Ideas for Book Review Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your book review videos. HookCut identifies key insight reveals, book myth busts, and applicability hooks in any book review YouTube content.",
  },
  {
    slug: "career",
    niche: "Career",
    intro:
      "Career Shorts that go viral challenge what viewers believe about job searching, workplace dynamics, or professional growth. The hooks that work in career content either expose a mistake most professionals are making or reveal a counterintuitive truth about how hiring, promotions, or workplace success actually work. HookCut identifies these moments in your career content.",
    hookTypes: [
      {
        type: "Career Myth Bust",
        description: "Challenge professional advice — 'Working harder is not how most people get promoted. Here's what actually works.'",
      },
      {
        type: "Hiring Insider",
        description: "Reveal what most job seekers don't know — 'HR screens resumes for 6 seconds. Here's what they're actually looking for.'",
      },
      {
        type: "Salary Reveal",
        description: "Create tension around compensation — 'I negotiated a 40% salary increase with one email. Here's exactly what I wrote.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the career insight — 'The one skill that separates people who get promoted from those who don't.'",
      },
      {
        type: "Workplace Reality",
        description: "Name something professionals experience but rarely discuss — 'Nobody tells you this about working in a big company.'",
      },
    ],
    failureReason:
      "Career videos fail as Shorts when they open with generic motivational content, vague professional advice, or slow context-setting about industries. The career hook must be specific — a number, a specific technique, or a reveal that contradicts what viewers have been told about professional success.",
    metaTitle: "YouTube Hook Ideas for Career Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your career videos. HookCut identifies career myth busts, hiring insights, and salary reveals in any career YouTube content.",
  },
  {
    slug: "language-learning",
    niche: "Language Learning",
    intro:
      "Language learning Shorts that go viral challenge the conventional wisdom about how languages are actually learned. The hooks that work expose a method that contradicts traditional study approaches, reveal a surprising fact about language acquisition, or create immediate curiosity about a technique. HookCut identifies these moments in your language learning content.",
    hookTypes: [
      {
        type: "Method Myth Bust",
        description: "Challenge common learning approaches — 'Studying grammar first is why most language learners plateau.'",
      },
      {
        type: "Acquisition Reveal",
        description: "Reveal a surprising fact about language learning — 'Babies don't learn language by studying it. Adults can use the same method.'",
      },
      {
        type: "Progress Proof",
        description: "Lead with a result — 'I became conversational in Japanese in 6 months without living in Japan.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the technique — 'The reason 95% of language learners never reach fluency — and how to avoid it.'",
      },
      {
        type: "Contrarian Advice",
        description: "Challenge popular tools — 'I stopped using Duolingo. My language learning accelerated.'",
      },
    ],
    failureReason:
      "Language learning videos fail as Shorts when they open with generic study tips, vocabulary reviews, or slow method explanations. The language learner who scrolls is already motivated — they stop for the specific insight that tells them why they're not progressing and what actually works.",
    metaTitle: "YouTube Hook Ideas for Language Learning Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your language learning videos. HookCut identifies method myth busts, acquisition reveals, and progress proof hooks in any language learning YouTube content.",
  },
  {
    slug: "history",
    niche: "History",
    intro:
      "History Shorts that go viral reveal something surprising that contradicts what viewers learned in school, or expose an unexpected connection between historical events and the present. The hooks in history content create immediate intellectual curiosity — a fact so counterintuitive that it demands an explanation. HookCut identifies these moments in your history content.",
    hookTypes: [
      {
        type: "History Myth Bust",
        description: "Correct a popular historical misconception — 'Napoleon was not short. The British propaganda campaign that created the myth.'",
      },
      {
        type: "Unknown History Reveal",
        description: "Surface forgotten history — 'The medieval queen who ruled Europe for 40 years that history forgot.'",
      },
      {
        type: "Modern Connection",
        description: "Connect history to now — 'This is the exact same economic pattern that preceded every major recession in the last 200 years.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue about an event — 'The single decision that could have prevented World War I.'",
      },
      {
        type: "Shock Statistic",
        description: "Use historical data unexpectedly — 'The Roman Empire was more diverse than most modern countries.'",
      },
    ],
    failureReason:
      "History videos fail as Shorts when they open with historical context, timeline setups, or textbook-style narration. The hook must create immediate curiosity — the surprising fact, the unknown story, or the counterintuitive claim that makes the viewer think 'I had no idea.'",
    metaTitle: "YouTube Hook Ideas for History Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your history videos. HookCut identifies history myth busts, unknown history reveals, and modern connections in any history YouTube content.",
  },
  {
    slug: "science",
    niche: "Science",
    intro:
      "Science Shorts that go viral make complex ideas immediately accessible through a surprising fact, a counterintuitive result, or a demonstration that challenges intuition. The hooks in science content are often the moment where reality contradicts expectation — where the science says something different from what common sense suggests. HookCut identifies these moments in your science content.",
    hookTypes: [
      {
        type: "Intuition Violation",
        description: "Challenge common sense — 'A pound of feathers is heavier than a pound of gold. Here's why.'",
      },
      {
        type: "Research Reveal",
        description: "Lead with a surprising study result — 'Scientists discovered that trees communicate with each other underground.'",
      },
      {
        type: "Demonstration Hook",
        description: "Open on a result that seems impossible — the experiment that creates immediate 'how?' tension.",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the scientific explanation — 'There's a lake in Africa that can kill anything that enters it. Scientists just figured out why.'",
      },
      {
        type: "Shock Statistic",
        description: "Use scientific scale to create awe — 'The number of atoms in a grain of sand exceeds all the grains of sand on Earth.'",
      },
    ],
    failureReason:
      "Science videos fail as Shorts when they open with lengthy scientific context, academic jargon, or slow experimental setup. The hook must create immediate wonder — the surprising fact, the counterintuitive result, or the demonstration that makes viewers stop and ask 'how is that possible?'",
    metaTitle: "YouTube Hook Ideas for Science Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your science videos. HookCut identifies intuition violations, research reveals, and demonstration hooks in any science YouTube content.",
  },
  {
    slug: "psychology",
    niche: "Psychology",
    intro:
      "Psychology Shorts that go viral name something viewers experience but have never had words for, or reveal a cognitive bias that immediately explains something in their own life. The hooks in psychology content create instant recognition — the moment where viewers think 'I do this, and now I understand why.' HookCut identifies these moments in your psychology content.",
    hookTypes: [
      {
        type: "Bias Reveal",
        description: "Name a cognitive bias that explains behavior — 'The reason you remember bad feedback more than good feedback has a name.'",
      },
      {
        type: "Behavior Explanation",
        description: "Explain a behavior viewers recognize — 'Why you can't stop checking your phone even when you want to.'",
      },
      {
        type: "Research Reveal",
        description: "Lead with a surprising study — 'A study put people in a room with mirrors. The results changed psychology.'",
      },
      {
        type: "Curiosity Gap",
        description: "Create intrigue around the mind — 'The psychological reason people stay in relationships they know are wrong.'",
      },
      {
        type: "Recognition Hook",
        description: "Name an experience — 'There's a word for the feeling of wanting to squeeze something cute. Psychology explains why.'",
      },
    ],
    failureReason:
      "Psychology videos fail as Shorts when they open with academic framing, slow concept explanations, or vague motivation ('your mindset matters'). The psychology hook must create immediate self-recognition — viewers stop when they see their own behavior or experience named and explained.",
    metaTitle: "YouTube Hook Ideas for Psychology Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your psychology videos. HookCut identifies bias reveals, behavior explanations, and recognition hooks in any psychology YouTube content.",
  },
  {
    slug: "productivity",
    niche: "Productivity",
    intro:
      "Productivity Shorts that go viral challenge the conventional wisdom about work, time, or attention — or reveal a specific technique that contradicts what most productivity advice recommends. The hooks that work in productivity content create either immediate recognition ('I have this exact problem') or genuine surprise ('I've never thought about it this way'). HookCut identifies these moments in your productivity content.",
    hookTypes: [
      {
        type: "System Myth Bust",
        description: "Challenge popular productivity advice — 'Your to-do list is making you less productive. Here's the data.'",
      },
      {
        type: "Technique Reveal",
        description: "Expose a specific method — 'The 2-minute rule changed how I handle email. Here's exactly how it works.'",
      },
      {
        type: "Time Reveal",
        description: "Create tension around time — 'I tracked every hour of my workday for 30 days. The results embarrassed me.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the technique — 'The one habit that separates high performers from everyone else.'",
      },
      {
        type: "Contrarian Productivity Take",
        description: "Challenge hustle culture — 'Working 80-hour weeks made me less productive. Here's what the research says.'",
      },
    ],
    failureReason:
      "Productivity videos fail as Shorts when they open with motivation speeches, vague system overviews, or slow walks through apps and tools. The productivity hook must be specific — a technique, a time reveal, or a counterintuitive claim. Generic advice ('plan your day') stops nobody.",
    metaTitle: "YouTube Hook Ideas for Productivity Creators | HookCut",
    metaDescription:
      "Find scroll-stopping moments in your productivity videos. HookCut identifies system myth busts, technique reveals, and contrarian productivity hooks in any productivity YouTube content.",
  },
  {
    slug: "personal-finance",
    niche: "Personal Finance",
    intro:
      "Personal finance Shorts that go viral make viewers feel either urgently aware of a mistake they're making or surprisingly hopeful about a financial path they didn't know existed. The hooks in personal finance content are often specific numbers, counterintuitive financial strategies, or painful recognitions of common financial mistakes. HookCut identifies these moments in your personal finance content.",
    hookTypes: [
      {
        type: "Money Mistake Reveal",
        description: "Expose a common financial error — 'If your emergency fund is in a regular savings account, you're losing money every year.'",
      },
      {
        type: "Net Worth Shock",
        description: "Create tension around numbers — 'The median net worth of a 35-year-old in India. And what to do if you're behind.'",
      },
      {
        type: "Strategy Reveal",
        description: "Lead with a specific financial strategy — 'I invested ₹5,000 a month for 10 years. Here's what the compounding actually looks like.'",
      },
      {
        type: "Contrarian Finance Advice",
        description: "Challenge conventional wisdom — 'Stop building an emergency fund first. Here's the order that actually maximizes returns.'",
      },
      {
        type: "Curiosity Gap",
        description: "Withhold the financial insight — 'The one account type that most Indians don't use — and it's tax-free.'",
      },
    ],
    failureReason:
      "Personal finance videos fail as Shorts when they open with budget spreadsheets, slow wealth-building context, or generic advice ('spend less than you earn'). The personal finance hook must create immediate financial relevance — a number that surprises, a mistake that resonates, or a strategy that makes viewers think 'I should have started this yesterday.'",
    metaTitle: "YouTube Hook Ideas for Personal Finance Creators | HookCut",
    metaDescription:
      "Find the viral hook moments in your personal finance videos. HookCut identifies money mistake reveals, net worth shocks, and strategy reveals in any personal finance YouTube content.",
  },
];

export function getNichePage(slug: string): NichePage | null {
  return nichePages.find((n) => n.slug === slug) ?? null;
}

export function getAllNicheSlugs(): string[] {
  return nichePages.map((n) => n.slug);
}
