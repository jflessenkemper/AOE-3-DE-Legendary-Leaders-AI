//==============================================================================
/* leader_usman.xs */
//==============================================================================

bool gUsmanRulesEnabled = false;

void initLeaderUsman(void)
{
   aiEcho("Legendary Leaders: activating Usman dan Fodio personality.");

   llSetAggressivePersonality();
   btRushBoom = 0.5;
   btOffenseDefense = 0.6;
   btBiasTrade = 0.2;
   btBiasNative = 0.3;
   llSetMilitaryFocus(0.4, 0.4, 0.0);
   cvMaxTowers = 4;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineIntegration, 0.32, 64.0);
   llEnablePrisonerSystem();
   gUsmanRulesEnabled = true;
   llLogLeaderState("Usman initialized");
}

rule usmanCaliphateExpansion
inactive
minInterval 75
{
   llLogRuleTick("usmanCaliphateExpansion");
   if (gUsmanRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge2)
   {
      btBiasCav = 0.6;
      btBiasTrade = 0.3;
   }
}

void enableLeaderUsmanRules(void)
{
   if (gUsmanRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("usmanCaliphateExpansion");
}