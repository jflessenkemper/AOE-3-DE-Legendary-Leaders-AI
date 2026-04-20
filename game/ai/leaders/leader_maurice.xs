//==============================================================================
/* leader_maurice.xs */
//==============================================================================

bool gMauriceRulesEnabled = false;

void initLeaderMaurice(void)
{
   llVerboseEcho("Legendary Leaders: activating Maurice of Nassau personality.");

   llSetDefensivePersonality();
   btRushBoom = -0.2;
   btOffenseDefense = -0.1;
   btBiasTrade = 0.5;
   btBiasNative = -0.2;
   llSetMilitaryFocus(0.5, 0.0, 0.2);
   cvMaxTowers = 5;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.22, 56.0);
   llEnablePrisonerSystem();
   gMauriceRulesEnabled = true;
   llLogLeaderState("Maurice initialized");
}

rule mauriceDrillReforms
inactive
minInterval 80
{
   llLogRuleTick("mauriceDrillReforms");
   if (gMauriceRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.7;
      btBiasTrade = 0.6;
   }
}

void enableLeaderMauriceRules(void)
{
   if (gMauriceRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("mauriceDrillReforms");
}
