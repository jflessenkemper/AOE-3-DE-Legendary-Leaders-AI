//==============================================================================
/* leader_shivaji.xs */
//==============================================================================

bool gShivajiRulesEnabled = false;

void initLeaderShivaji(void)
{
   aiEcho("Legendary Leaders: activating Shivaji Maharaj personality.");

   llSetBalancedPersonality();
   btRushBoom = 0.2;
   btOffenseDefense = 0.3;
   btBiasTrade = 0.1;
   btBiasNative = 0.1;
   llSetMilitaryFocus(0.5, 0.2, 0.2);
   cvMaxTowers = 3;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExchange, 0.24, 58.0);
   llEnablePrisonerSystem();
   gShivajiRulesEnabled = true;
   llLogLeaderState("Shivaji initialized");
}

rule shivajiMobileStatecraft
inactive
minInterval 75
{
   llLogRuleTick("shivajiMobileStatecraft");
   if (gShivajiRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (kbGetAge() >= cAge3)
   {
      btBiasInf = 0.6;
      btBiasCav = 0.4;
   }
}

void enableLeaderShivajiRules(void)
{
   if (gShivajiRulesEnabled == false)
   {
      return;
   }

   xsEnableRule("shivajiMobileStatecraft");
}