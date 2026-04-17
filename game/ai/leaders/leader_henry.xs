//==============================================================================
/* leader_henry.xs */
//==============================================================================

bool gHenryRulesEnabled = false;

void initLeaderHenry(void)
{
   aiEcho("Legendary Leaders: activating Prince Henry the Navigator personality.");

   llSetBalancedPersonality();
   btRushBoom = -0.2;
   btOffenseDefense = 0.0;
   btBiasTrade = 0.6;
   btBiasNative = 0.1;
   llSetMilitaryFocus(0.2, 0.1, 0.4);
   cvOkToTrainNavy = true;
   llSetPrisonerDoctrine(cLLPrisonerDoctrineExchange, 0.20, 54.0);
   llEnablePrisonerSystem();
   gHenryRulesEnabled = true;
   llLogLeaderState("Henry initialized");
}

rule henryOverseasEmpire
inactive
minInterval 75
{
   llLogRuleTick("henryOverseasEmpire");
   if (gHenryRulesEnabled == false)
   {
      xsDisableSelf();
      return;
   }

   if (gWaterMap == true)
   {
      btBiasTrade = 0.8;
      btBiasArt = 0.5;
   }
}

void enableLeaderHenryRules(void)
{
   if (gHenryRulesEnabled == false)
   {
      return;
   }
   xsEnableRule("henryOverseasEmpire");
}
