//==============================================================================
/* leader_kangxi.xs */
//==============================================================================

bool gKangxiRulesEnabled = false;

void initLeaderKangxi(void)
{
   aiEcho("Legendary Leaders: activating Kangxi Emperor personality.");

   llSetBalancedPersonality();
   btRushBoom = 0.1;
   btOffenseDefense = 0.2;
   btBiasTrade = 0.2;
   btBiasNative = -0.1;
   llSetMilitaryFocus(0.5, 0.0, 0.4);
   cvMaxTowers = 4;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineStrictImprisonment, 0.24, 60.0);
   llEnablePrisonerSystem();
   gKangxiRulesEnabled = true;
}

rule kangxiBannerDiscipline
inactive
minInterval 80
{
   if (gKangxiRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.6;
      btBiasArt = 0.4;
   }
}

void enableLeaderKangxiRules(void)
{
   if (gKangxiRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("kangxiBannerDiscipline");
}