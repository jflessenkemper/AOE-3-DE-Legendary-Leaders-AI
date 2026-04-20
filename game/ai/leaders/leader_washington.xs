//==============================================================================
/* leader_washington.xs */
//==============================================================================

bool gWashingtonRulesEnabled = false;

void initLeaderWashington(void)
{
   llVerboseEcho("Legendary Leaders: activating George Washington personality.");

   llSetBalancedPersonality();
   btRushBoom = 0.2;
   btOffenseDefense = 0.1;
   btBiasTrade = -0.2;
   btBiasNative = 0.0;
   llSetMilitaryFocus(0.5, 0.1, 0.2);
   cvMaxTowers = 4;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExchange, 0.20, 54.0);
   llEnablePrisonerSystem();
   gWashingtonRulesEnabled = true;
   llLogLeaderState("Washington initialized");
}

rule washingtonContinentalArmy
inactive
minInterval 80
{
   llLogRuleTick("washingtonContinentalArmy");
   if (gWashingtonRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.6;
      btBiasArt = 0.3;
   }
}

void enableLeaderWashingtonRules(void)
{
   if (gWashingtonRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("washingtonContinentalArmy");
}
