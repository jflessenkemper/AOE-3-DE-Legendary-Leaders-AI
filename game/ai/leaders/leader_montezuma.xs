//==============================================================================
/* leader_montezuma.xs */
//==============================================================================

bool gMontezumaRulesEnabled = false;

void initLeaderMontezuma(void)
{
   aiEcho("Legendary Leaders: activating Montezuma II personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.6;
   btOffenseDefense = 0.7;
   btBiasTrade = -0.4;
   btBiasNative = 0.3;
   llSetMilitaryFocus(0.8, -0.2, 0.0);
   cvMaxTowers = 3;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExecution, 0.40, 72.0);
   llEnablePrisonerSystem();
   gMontezumaRulesEnabled = true;
   llLogLeaderState("Montezuma initialized");
}

rule montezumaFlowerWars
inactive
minInterval 70
{
   llLogRuleTick("montezumaFlowerWars");
   if (gMontezumaRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasInf = 0.8;
      btBiasCav = 0.4;
   }
}

void enableLeaderMontezumaRules(void)
{
   if (gMontezumaRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("montezumaFlowerWars");
}