//==============================================================================
/* leader_napoleon.xs

   Napoleon Bonaparte - Napoleonic France master personality.
*/
//==============================================================================

bool gNapoleonRulesEnabled = false;

void initLeaderNapoleon(void)
{
   llVerboseEcho("Legendary Leaders: activating Napoleon Bonaparte personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.7;
   btOffenseDefense = 0.9;
   btBiasTrade = -0.2;
   btBiasNative = -0.4;
   llSetMilitaryFocus(0.2, 0.4, 0.6);
   llSetLeaderTacticalDoctrine(0.56, 0.68, 1, 0.0);

   cvMaxTowers = 4;
   cvOkToBuildForts = true;
   cvDefenseReflexRadiusActive = 80.0;
   cvDefenseReflexSearchRadius = 80.0;
   cvDefenseReflexRadiusPassive = 28.0;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineForcedLabor, 0.35, 72.0);
   llEnablePrisonerSystem();

   gNapoleonRulesEnabled = true;
   llLogLeaderState("Napoleon initialized");
}

rule napoleonGrandBattery
inactive
minInterval 45
{
   llLogRuleTick("napoleonGrandBattery");
   if (gNapoleonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasArt = 0.8;
      btBiasCav = 0.3;
      btBiasInf = 0.2;
   }
}

rule napoleonContinentalSystem
inactive
minInterval 60
{
   llLogRuleTick("napoleonContinentalSystem");
   if (gNapoleonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if ((kbGetAge() >= cAge2) && (btBiasTrade > -0.6))
   {
      btBiasTrade = -0.6;
   }
}

rule napoleonImperialTempo
inactive
minInterval 90
{
   llLogRuleTick("napoleonImperialTempo");
   if (gNapoleonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge4)
   {
      cvMaxArmyPop = 140;
      btRushBoom = 0.4;
      llEnableForwardBaseStyle();
   }
}

void enableLeaderNapoleonRules(void)
{
   if (gNapoleonRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("napoleonGrandBattery");
   xsEnableRule("napoleonContinentalSystem");
   xsEnableRule("napoleonImperialTempo");
}
