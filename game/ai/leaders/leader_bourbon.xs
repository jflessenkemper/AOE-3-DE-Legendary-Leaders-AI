//==============================================================================
/* leader_bourbon.xs

   Louis XVIII - Royal France restoration personality.
*/
//==============================================================================

bool gBourbonRulesEnabled = false;

void initLeaderBourbon(void)
{
   llVerboseEcho("Legendary Leaders: activating Louis XVIII personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.3;
   btOffenseDefense = -0.4;
   btBiasTrade = 0.4;
   btBiasNative = -0.4;
   llSetMilitaryFocus(0.4, 0.3, 0.2);

   cvMaxTowers = 5;
   cvOkToBuildForts = true;
   cvDefenseReflexRadiusActive = 72.0;
   cvDefenseReflexSearchRadius = 72.0;
   cvDefenseReflexRadiusPassive = 30.0;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.26, 60.0);
   llEnablePrisonerSystem();

   gBourbonRulesEnabled = true;
   llLogLeaderState("Bourbon initialized");
}

rule bourbonCourtEconomy
inactive
minInterval 60
{
   llLogRuleTick("bourbonCourtEconomy");
   if (gBourbonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasTrade = 0.6;
      btRushBoom = -0.4;
   }
}

rule bourbonRoyalArmy
inactive
minInterval 80
{
   llLogRuleTick("bourbonRoyalArmy");
   if (gBourbonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.5;
      btBiasCav = 0.5;
      btBiasArt = 0.2;
   }
}

rule bourbonRestorationFront
inactive
minInterval 90
{
   llLogRuleTick("bourbonRestorationFront");
   if (gBourbonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge4)
   {
      cvMaxArmyPop = 130;
      cvMaxTowers = 6;
   }
}

void enableLeaderBourbonRules(void)
{
   if (gBourbonRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("bourbonCourtEconomy");
   xsEnableRule("bourbonRoyalArmy");
   xsEnableRule("bourbonRestorationFront");
}