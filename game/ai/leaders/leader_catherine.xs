//==============================================================================
/* leader_catherine.xs

   Yekaterina Alexeyevna Romanova - Catherine II "the Great" of Russia,
   enlightened-absolutist personality at the height of imperial expansion.

   Historical doctrine:
     - Russo-Turkish wars (1768-1792): Catherine's armies under Rumyantsev
       and Suvorov bulldozed the southern frontier with line-infantry mass
       and combined-arms columns. Mapped to a deep infantry bias and a
       moderate cavalry weight (Cossack hetmans on the wings).
     - Streltsy and Musketeer block: Russian civ trains infantry in cheap
       blocks rather than singletons. Mapped to a very high infantry mass
       cap and a strong infantry weight from Colonial on.
     - Cossack frontier cavalry: irregular hetmans guarding the steppe.
       Mapped to a real cavalry share that supports rather than leads.
     - Pomestnoye estate economy: serfs feed the army through landed
       gentry. Mapped to a Distributed Economic Network style and a
       moderate Trade Route lean.
     - Enlightenment statecraft: tolerance for non-Russian peoples on the
       expansion frontier. Mapped to a small Native Treaty lean.
*/
//==============================================================================

bool gCatherineRulesEnabled = false;

void initLeaderCatherine(void)
{
   llVerboseEcho("Legendary Leaders: activating Catherine the Great personality.");

   llSetBalancedPersonality();
   btRushBoom = -0.2;             // Moderate boom; Russian blocks come cheap.
   btOffenseDefense = 0.45;
   btBiasTrade = 0.3;
   btBiasNative = 0.1;
   llSetMilitaryFocus(0.85, 0.35, 0.4);  // Infantry-led, supporting cavalry, real artillery.

   // LL-BUILD-STYLE-BEGIN
   llUseCossackVoiskoStyle(1);
   llSetBuildStrongpointProfile(2, 2, 3, true);
   // LL-BUILD-STYLE-END
   llSetLeaderTacticalDoctrine(0.78, 0.22, 2, 4.0);

   cvOkToBuildForts = true;
   cvMaxTowers = 5;
   cvMaxArmyPop = 130;            // Russian mass.

   gCatherineRulesEnabled = true;
   llLogLeaderState("Catherine initialized");
}

//------------------------------------------------------------------------------
// Discovery: Pomestnoye boom. Settler push and Trade Post placement;
// the gentry organize the rural economy.
//------------------------------------------------------------------------------
rule catherinePomestnoyeBoom
inactive
minInterval 60
{
   llLogRuleTick("catherinePomestnoyeBoom");
   if (gCatherineRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() <= cAge1)
   {
      btRushBoom = -0.4;
      btBiasTrade = 0.45;
      cvMinNumVills = 18;
   }
}

//------------------------------------------------------------------------------
// Colonial: Streltsy block. Streltsy musket mass and Cossack screen,
// forward base posture; the army assembles in depth.
//------------------------------------------------------------------------------
rule catherineStreltsyBlock
inactive
minInterval 50
{
   llLogRuleTick("catherineStreltsyBlock");
   if (gCatherineRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge2)
   {
      btRushBoom = -0.05;
      btOffenseDefense = 0.5;
      btBiasInf = 0.95;            // Block infantry mass.
      btBiasCav = 0.4;             // Cossack hetmans.
      btBiasArt = -0.1;
      llEnableForwardBaseStyle();
   }
}

//------------------------------------------------------------------------------
// Fortress: Imperial Expansion. Musketeer line, Oprichnik shock, Cossack
// flank, Falconet support. Suvorov-style combined-arms columns.
//------------------------------------------------------------------------------
rule catherineImperialExpansion
inactive
minInterval 55
{
   llLogRuleTick("catherineImperialExpansion");
   if (gCatherineRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge3)
   {
      btOffenseDefense = 0.7;
      btBiasInf = 1.0;
      btBiasCav = 0.55;
      btBiasArt = 0.5;
      cvMaxArmyPop = 145;
   }
}

//------------------------------------------------------------------------------
// Industrial: Russo-Turkish campaign. Heavy Cannon park, Musketeer mass,
// Cossack and Oprichnik mounted reserve. The empire crushes by depth.
//------------------------------------------------------------------------------
rule catherineRussoTurkishCampaign
inactive
minInterval 70
{
   llLogRuleTick("catherineRussoTurkishCampaign");
   if (gCatherineRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() == cAge4)
   {
      btOffenseDefense = 0.85;
      btBiasInf = 1.0;
      btBiasCav = 0.65;
      btBiasArt = 0.7;
      cvMaxArmyPop = 160;
      llEnableForwardBaseStyle();
   }
}

//------------------------------------------------------------------------------
// Imperial: Romanov supremacy - maximum Musketeer / Strelet / Heavy Cannon
// mass with continuous Cossack pressure on the wings.
//------------------------------------------------------------------------------
rule catherineRomanovSupremacy
inactive
minInterval 90
{
   llLogRuleTick("catherineRomanovSupremacy");
   if (gCatherineRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge5)
   {
      btOffenseDefense = 0.95;
      btBiasInf = 1.0;
      btBiasCav = 0.7;
      btBiasArt = 0.85;
      cvMaxArmyPop = 175;
   }
}

void enableLeaderCatherineRules(void)
{
   if (gCatherineRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("catherinePomestnoyeBoom");
   xsEnableRule("catherineStreltsyBlock");
   xsEnableRule("catherineImperialExpansion");
   xsEnableRule("catherineRussoTurkishCampaign");
   xsEnableRule("catherineRomanovSupremacy");
}
