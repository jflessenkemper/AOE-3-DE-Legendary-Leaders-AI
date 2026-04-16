//==============================================================================
/* leader_hiawatha.xs */
//==============================================================================

bool gHiawathaRulesEnabled = false;

void initLeaderHiawatha(void)
{
   aiEcho("Legendary Leaders: activating Hiawatha personality.");

   llSetBalancedPersonality();
   btRushBoom = 0.3;
   btOffenseDefense = 0.2;
   btBiasTrade = -0.1;
   btBiasNative = 0.5;
   llSetMilitaryFocus(0.7, -0.1, 0.0);
   cvMaxTowers = 3;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineIntegration, 0.30, 62.0);
   llEnablePrisonerSystem();
   gHiawathaRulesEnabled = true;
}

rule hiawathaConfederacyWarbands
inactive
minInterval 75
{
   if (gHiawathaRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasInf = 0.7;
      btBiasNative = 0.7;
   }
}

void enableLeaderHiawathaRules(void)
{
   if (gHiawathaRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("hiawathaConfederacyWarbands");
}