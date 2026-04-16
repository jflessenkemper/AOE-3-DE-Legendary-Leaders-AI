//==============================================================================
/* leader_catherine.xs */
//==============================================================================

bool gCatherineRulesEnabled = false;

void initLeaderCatherine(void)
{
   aiEcho("Legendary Leaders: activating Catherine the Great personality.");

   llSetBalancedPersonality();
   btRushBoom = -0.1;
   btOffenseDefense = 0.2;
   btBiasTrade = 0.3;
   llSetMilitaryFocus(0.6, 0.1, -0.1);
   cvMaxTowers = 5;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineForcedLabor, 0.32, 68.0);
   llEnablePrisonerSystem();
   gCatherineRulesEnabled = true;
}

rule catherineImperialExpansion
inactive
minInterval 90
{
   if (gCatherineRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      cvMaxCivPop = 95;
      btBiasInf = 0.7;
   }
}

void enableLeaderCatherineRules(void)
{
   if (gCatherineRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("catherineImperialExpansion");
}
