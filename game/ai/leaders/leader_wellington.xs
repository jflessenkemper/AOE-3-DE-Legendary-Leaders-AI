//==============================================================================
/* leader_wellington.xs

   Arthur Wellesley, 1st Duke of Wellington - British line-and-logistics
   personality.

   Historical doctrine:
     - Thin red line: two-deep volley fire and hollow infantry squares
       against cavalry. Translates to overwhelming line-infantry mass
       (Musketeer / Longbowman) anchored by drilled discipline.
     - Reverse slope: deployed line infantry behind hill crests to shelter
       from enemy artillery, then crested at point-blank range. Mapped
       here to defensive posture with strong forward-base anchors instead
       of open-field assaults.
     - Logistics first: never advanced without supply secured (Lines of
       Torres Vedras, Iberian campaign). Mapped to a heavy Manor economy
       and fortification investment.
     - Combined arms: Light Division riflemen screened, line infantry
       held the centre, KGL hussars and dragoons counter-charged, and
       Royal Artillery served the flanks.
     - Iron Duke temperament: cool, methodical, allergic to wasted men.
       Mapped to a defensive personality with high army efficiency and
       low willingness to commit elites first.
*/
//==============================================================================

bool gWellingtonRulesEnabled = false;

void initLeaderWellington(void)
{
   llVerboseEcho("Legendary Leaders: activating Duke of Wellington personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.35;            // Boom over rush; secure the supply line.
   btOffenseDefense = 0.25;       // Defensive baseline; scales up by age.
   btBiasTrade = 0.3;             // Royal Navy / commerce bias.
   btBiasNative = -0.2;           // Wellington trusted Iberian regulars more than auxiliaries.
   llSetMilitaryFocus(0.7, 0.05, 0.25);  // Infantry-led, modest cavalry, real artillery.

   // LL-BUILD-STYLE-BEGIN
   llUseNavalMercantileCompoundStyle(2);
   gLLEconomicDistanceMultiplier = 1.30;
   // LL-BUILD-STYLE-END
   llSetLeaderTacticalDoctrine(0.82, 0.18, 2, 4.0);   // Leader well behind the firing line.

   cvOkToBuildForts = true;
   cvMaxTowers = 6;
   cvMaxArmyPop = 110;

   gWellingtonRulesEnabled = true;
   llLogLeaderState("Wellington initialized");
}

//------------------------------------------------------------------------------
// Discovery: Manor boom and explorer scouting. Wellington spent weeks
// surveying ground before any campaign - reflected as heavy scouting and
// villager push.
//------------------------------------------------------------------------------
rule wellingtonManorBoom
inactive
minInterval 60
{
   llLogRuleTick("wellingtonManorBoom");
   if (gWellingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() <= cAge1)
   {
      btRushBoom = -0.6;          // Hard boom into Colonial.
      btBiasTrade = 0.45;         // Trade Route emphasis - Royal Navy doctrine.
      cvMinNumVills = 18;
   }
}

//------------------------------------------------------------------------------
// Colonial: Longbowmen as area-denial skirmishers, fast Manor sprawl, light
// Hussar screen. Wellington avoided early adventure - hold ground and grow.
//------------------------------------------------------------------------------
rule wellingtonLongbowScreen
inactive
minInterval 50
{
   llLogRuleTick("wellingtonLongbowScreen");
   if (gWellingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge2)
   {
      btRushBoom = -0.1;
      btOffenseDefense = 0.35;
      btBiasInf = 0.85;           // Longbow + transitional musket presence.
      btBiasCav = 0.1;            // Light Hussar screen.
      btBiasArt = -0.4;           // No real artillery yet; save xp.
      cvMinNumVills = 30;
   }
}

//------------------------------------------------------------------------------
// Fortress: the Redcoat (Musketeer) age. Drilled line infantry mass with
// Falconet flank support and KGL Hussar / Dragoon counter-charge. Forward
// base anchored well within own defensive perimeter (the Lines of Torres
// Vedras analogue).
//------------------------------------------------------------------------------
rule wellingtonRedcoatLine
inactive
minInterval 55
{
   llLogRuleTick("wellingtonRedcoatLine");
   if (gWellingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge3)
   {
      btOffenseDefense = 0.55;
      btBiasInf = 1.0;            // Redcoat mass.
      btBiasCav = 0.35;           // KGL Hussar / Dragoon counter-strike.
      btBiasArt = 0.5;            // Falconet support arrives.
      cvMaxArmyPop = 125;
      llEnableForwardBaseStyle();
   }
}

//------------------------------------------------------------------------------
// Industrial: Iberian-Peninsula style. Ranger mercenaries from the Saloon,
// Heavy Cannon punch, dense Manor sprawl. The army stops being defensive
// and starts grinding the front line forward in disciplined steps.
//------------------------------------------------------------------------------
rule wellingtonIberianGrind
inactive
minInterval 70
{
   llLogRuleTick("wellingtonIberianGrind");
   if (gWellingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge4)
   {
      btOffenseDefense = 0.7;
      btBiasInf = 1.0;
      btBiasCav = 0.3;
      btBiasArt = 0.7;            // Heavy Cannon and Howitzer share rises.
      cvMaxArmyPop = 140;
      cvMaxTowers = 8;
   }
}

//------------------------------------------------------------------------------
// Imperial: Iron Duke fortified-line warfare. Maximum Redcoat plus Heavy
// Cannon weight, KGL cavalry reserves, fort-anchored advance. Wellington
// at Waterloo: stand the line, let them break, then walk forward.
//------------------------------------------------------------------------------
rule wellingtonIronDuke
inactive
minInterval 90
{
   llLogRuleTick("wellingtonIronDuke");
   if (gWellingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge5)
   {
      btRushBoom = -0.05;         // Still some eco growth, mostly army.
      btOffenseDefense = 0.85;
      btBiasInf = 1.0;
      btBiasCav = 0.4;
      btBiasArt = 0.9;            // Maximum artillery commitment.
      cvMaxArmyPop = 160;
      llEnableForwardBaseStyle();
   }
}

void enableLeaderWellingtonRules(void)
{
   if (gWellingtonRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("wellingtonManorBoom");
   xsEnableRule("wellingtonLongbowScreen");
   xsEnableRule("wellingtonRedcoatLine");
   xsEnableRule("wellingtonIberianGrind");
   xsEnableRule("wellingtonIronDuke");
}
