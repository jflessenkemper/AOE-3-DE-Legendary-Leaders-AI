//==============================================================================
/* leader_frederick.xs */
//==============================================================================

bool gFrederickRulesEnabled = false;

void initLeaderFrederick(void)
{
   llVerboseEcho("Legendary Leaders: activating Frederick the Great personality.");

   llSetBalancedPersonality();
   btRushBoom = 0.2;
   btOffenseDefense = 0.4;
   btBiasTrade = -0.2;
   llSetMilitaryFocus(0.5, 0.4, 0.2);
   cvMaxTowers = 3;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.28, 62.0);
   llEnablePrisonerSystem();
   gFrederickRulesEnabled = true;
   llLogLeaderState("Frederick initialized");
}

rule frederickObliqueOrder
inactive
minInterval 75
{
   llLogRuleTick("frederickObliqueOrder");
   if (gFrederickRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.6;
      btBiasCav = 0.5;
   }
}

void enableLeaderFrederickRules(void)
{
   if (gFrederickRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("frederickObliqueOrder");
}
