//==============================================================================
/* leader_menelik.xs */
//==============================================================================

bool gMenelikRulesEnabled = false;

void initLeaderMenelik(void)
{
   aiEcho("Legendary Leaders: activating Menelik II personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.4;
   btOffenseDefense = 0.5;
   btBiasTrade = 0.1;
   btBiasNative = 0.1;
   llSetMilitaryFocus(0.6, -0.1, 0.4);
   cvOkToBuildForts = true;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineForcedLabor, 0.30, 66.0);
   llEnablePrisonerSystem();
   gMenelikRulesEnabled = true;
   llLogLeaderState("Menelik initialized");
}

rule menelikHighlandModernization
inactive
minInterval 80
{
   llLogRuleTick("menelikHighlandModernization");
   if (gMenelikRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.7;
      btBiasArt = 0.4;
   }
}

void enableLeaderMenelikRules(void)
{
   if (gMenelikRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("menelikHighlandModernization");
}