# === УРОВЕНЬ 4: ГЛУБОКИЙ ONCHAIN АНАЛИЗ ===
self.logger.info(f"УРОВЕНЬ 4: OnChain анализ топ-{len(top_candidates)} кандидатов...")

onchain_enriched_candidates = []
onchain_calls_used = 0

for i, item in enumerate(top_candidates):
    try:
        candidate = item['candidate']
        current_score = item['final_score']
        
        # Проверяем, стоит ли тратить OnChain ресурсы
        available_onchain_calls = self.api_tracker.rpc_daily_limit - self.api_tracker.rpc_calls_today
        
        if should_run_onchain_analysis(current_score, available_onchain_calls):
            self.logger.info(f"   OnChain анализ #{i+1}: {candidate.base_token_symbol} ({current_score} баллов)")
            
            # Выполняем OnChain анализ
            onchain_result = await self.onchain_agent.analyze_token(
                network=candidate.chain_id,
                token_address=candidate.base_token_address,
                lp_address=candidate.pair_address
            )
            
            onchain_calls_used += onchain_result.api_calls_used
            self.api_tracker.rpc_calls_today += onchain_result.api_calls_used
            self.api_tracker.etherscan_calls_today += 2  # Estimated calls for holders
            
            # Обновляем indicators с OnChain данными
            updated_indicators = item['indicators']
            updated_indicators.onchain_analysis = onchain_result
            
            # Пересчитываем score с OnChain данными
            updated_matrix = RealisticScoringMatrix(indicators=updated_indicators)
            updated_analysis = updated_matrix.get_detailed_analysis()
            updated_score = updated_analysis['total_score']
            
            # Логируем результат OnChain анализа
            score_change = updated_score - current_score
            risk_status = onchain_result.overall_risk.value
            
            if score_change > 0:
                self.logger.info(f"     OnChain результат: +{score_change} баллов (риск: {risk_status})")
            else:
                self.logger.info(f"     OnChain результат: {score_change} баллов (риск: {risk_status})")
            
            # Логируем детали OnChain анализа
            if onchain_result.lp_analysis:
                lp_lock = onchain_result.lp_analysis.locked_percentage + onchain_result.lp_analysis.dead_percentage
                self.logger.info(f"     LP блокировка: {lp_lock:.1f}% ({onchain_result.lp_analysis.risk_level.value})")
            
            if onchain_result.holder_analysis:
                concentration = onchain_result.holder_analysis.top_10_concentration
                self.logger.info(f"     Концентрация топ-10: {concentration:.1f}% ({onchain_result.holder_analysis.risk_level.value})")
            
            onchain_enriched_candidates.append({
                'candidate': candidate,
                'final_score': updated_score,
                'recommendation': updated_analysis['recommendation'],
                'analysis': updated_analysis,
                'indicators': updated_indicators,
                'onchain_result': onchain_result
            })
            
        else:
            # Пропускаем OnChain анализ, но сохраняем кандидата
            reason = "низкий балл" if current_score < 70 else "нехватка API calls"
            self.logger.debug(f"   Пропуск OnChain для {candidate.base_token_symbol}: {reason}")
            
            onchain_enriched_candidates.append(item)
            
    except Exception as e:
        self.logger.error(f"   Ошибка OnChain анализа для {candidate.base_token_symbol}: {e}")
        # В случае ошибки сохраняем кандидата без OnChain данных
        onchain_enriched_candidates.append(item)
        continue

self.logger.info(f"   OnChain анализ завершен. Использовано {onchain_calls_used} RPC calls.")

# Пересортировка после OnChain анализа
onchain_enriched_candidates.sort(key=lambda x: x['final_score'], reverse=True)

# Применяем фильтр качества
high_quality_candidates = [
    item for item in onchain_enriched_candidates 
    if item['final_score'] >= FUNNEL_CONFIG['min_score_for_alert']
]

self.logger.info(f"   {len(high_quality_candidates)} кандидатов прошли фильтр качества (>={FUNNEL_CONFIG['min_score_for_alert']} баллов)")
