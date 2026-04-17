//==============================================================================
/* leader_hidalgo.xs */
//==============================================================================

bool gHidalgoRulesEnabled = false;

void initLeaderHidalgo(void)
{
   aiEcho("Legendary Leaders: activating Miguel Hidalgo personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.4;
   btOffenseDefense = 0.5;
   btBiasTrade = -0.3;
   btBiasNative = 0.0;
   llSetMilitaryFocus(0.6, -0.1, 0.2);
   cvMaxTowers = 3;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineIntegration, 0.33, 68.0);
   llEnablePrisonerSystem();
   gHidalgoRulesEnabled = true;
   llLogLeaderState("Hidalgo initialized");
}

rule hidalgoInsurgentMomentum
inactive
minInterval 80
{
   llLogRuleTick("hidalgoInsurgentMomentum");
   if (gHidalgoRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasInf = 0.7;
      btOffenseDefense = 0.6;
   }
}

void enableLeaderHidalgoRules(void)
{
   if (gHidalgoRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("hidalgoInsurgentMomentum");
}
