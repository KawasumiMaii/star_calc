from typing import List, Callable
import math # 用于 math.isclose 或 abs 进行断言

def calculate_outgoing_damage(
    skill_multiplier: float,
    scaling_attribute_value: float,
    extra_multiplier: float,
    extra_dmg: float,
    elemental_dmg_bonus_percent: float,
    all_type_dmg_bonus_percent: float,
    dot_dmg_bonus_percent: float,
    other_dmg_bonus_percent: float,
    attacker_level: int,
    enemy_base_def: float,
    enemy_def_percent_buffs_debuffs: float,
    def_reduction_percent: float,
    def_ignore_percent: float,
    enemy_current_res_percent: float,
    res_pen_percent: float,
    elemental_dmg_taken_bonus_percent: float,
    all_type_dmg_taken_bonus_percent: float,
    universal_dmg_reduction_sources: List[float],
    weaken_percent: float,
) -> float:
    """
    根据各种战斗参数计算最终输出伤害。

    Args:
        skill_multiplier: 技能的伤害倍率 (例如, 0.6 代表 60%)。
        scaling_attribute_value: 角色属性（攻击力、生命值或防御力）的数值。
        extra_multiplier: 额外的伤害倍率 (例如, 0.2 代表 20%)。
        extra_dmg: 额外的固定伤害值。
        elemental_dmg_bonus_percent: 元素伤害加成百分比 (例如, 0.258 代表 25.8%)。
        all_type_dmg_bonus_percent: 全类型伤害加成百分比 (例如, 0.1 代表 10%)。
        dot_dmg_bonus_percent: 持续伤害 (DoT) 加成百分比 (例如, 0.12 代表 12%)。
        other_dmg_bonus_percent: 其他杂项伤害加成百分比。
        attacker_level: 攻击者的角色等级。
        enemy_base_def: 敌人的基础防御值。
        enemy_def_percent_buffs_debuffs: 敌人防御百分比增益或减益 (例如, 0.2 代表 20% 增益, -0.1 代表 10% 减益)。
        def_reduction_percent: 防御降低百分比 (例如, 0.15 代表 15%)。
        def_ignore_percent: 防御忽略百分比 (例如, 0.2 代表 20%)。
        enemy_current_res_percent: 敌人当前抗性百分比 (例如, 0.2 代表 20%)。
        res_pen_percent: 抗性穿透百分比 (例如, 0.1 代表 10%)。
        elemental_dmg_taken_bonus_percent: 元素伤害承伤加成百分比 (例如, 0.1 代表 10%)。
        all_type_dmg_taken_bonus_percent: 全类型伤害承伤加成百分比 (例如, 0.05 代表 5%)。
        universal_dmg_reduction_sources: 通用伤害减免来源列表 (例如, [0.1, 0.05] 代表 10% 和 5% 减免)。
        weaken_percent: 虚弱百分比 (例如, 0.15 代表 15%)。

    Returns:
        最终计算出的输出伤害。
    """

    # 1. 基础伤害
    base_dmg = (skill_multiplier + extra_multiplier) * scaling_attribute_value + extra_dmg

    # 2. 伤害百分比乘数
    dmg_percent_multiplier = (
        1
        + elemental_dmg_bonus_percent
        + all_type_dmg_bonus_percent
        + dot_dmg_bonus_percent
        + other_dmg_bonus_percent
    )

    # 3. 敌人最终防御
    enemy_final_def = enemy_base_def * (
        1 + enemy_def_percent_buffs_debuffs - (def_reduction_percent + def_ignore_percent)
    )
    enemy_final_def = max(0, enemy_final_def)  # 防御力不能低于0

    # 4. 防御乘数
    # 使用 Prydwen 公式: 防御乘数 = 1 - [敌人最终防御 / (敌人最终防御 + 200 + 10 * 攻击者等级)]
    def_multiplier_denominator = enemy_final_def + 200 + (10 * attacker_level)
    if def_multiplier_denominator == 0: # 避免除以零，尽管在 200 + 10 * 攻击者等级 的情况下不太可能发生
        def_multiplier = 1
    else:
        def_multiplier = 1 - (enemy_final_def / def_multiplier_denominator)


    # 5. 抗性乘数
    # (敌人当前抗性百分比 - 抗性穿透百分比) 应被限制在 -1.0 和 0.9 之间。
    # 然后 抗性乘数 = 1 - 限制后的值。
    effective_res = enemy_current_res_percent - res_pen_percent
    clamped_effective_res = max(-1.0, min(0.9, effective_res))
    res_multiplier = 1 - clamped_effective_res

    # 6. 承伤乘数
    dmg_taken_multiplier = (
        1 + elemental_dmg_taken_bonus_percent + all_type_dmg_taken_bonus_percent
    )

    # 7. 通用减伤乘数
    universal_dmg_reduction_multiplier = 1.0
    for reduction_source in universal_dmg_reduction_sources:
        universal_dmg_reduction_multiplier *= (1 - reduction_source)

    # 8. 虚弱乘数
    weaken_multiplier = 1 - weaken_percent

    # 最终输出伤害计算
    outgoing_dmg = (
        base_dmg
        * dmg_percent_multiplier
        * def_multiplier
        * res_multiplier
        * dmg_taken_multiplier
        * universal_dmg_reduction_multiplier
        * weaken_multiplier
    )

    return outgoing_dmg

def calculate_total_atk(char_base_atk: float, lc_base_atk: float, atk_percent_bonus: float, flat_atk_bonus: float) -> float:
    """
    计算角色的总攻击力 (ATK)。

    公式: 总攻击力 = (角色基础攻击力 + 光锥基础攻击力) * (1 + 攻击力百分比加成) + 攻击力固定值加成

    Args:
        char_base_atk: 角色的基础攻击力。
        lc_base_atk: 光锥的基础攻击力。
        atk_percent_bonus: 所有百分比攻击力加成的总和 (例如, 0.48 代表 48%)。
        flat_atk_bonus: 所有固定攻击力加成的总和。

    Returns:
        计算出的总攻击力值。
    """
    total_atk = (char_base_atk + lc_base_atk) * (1 + atk_percent_bonus) + flat_atk_bonus
    return total_atk

def calculate_total_hp(char_base_hp: float, lc_base_hp: float, hp_percent_bonus: float, flat_hp_bonus: float) -> float:
    """
    计算角色的总生命值 (HP)。

    公式: 总生命值 = (角色基础生命值 + 光锥基础生命值) * (1 + 生命值百分比加成) + 生命值固定值加成

    Args:
        char_base_hp: 角色的基础生命值。
        lc_base_hp: 光锥的基础生命值。
        hp_percent_bonus: 所有百分比生命值加成的总和 (例如, 0.48 代表 48%)。
        flat_hp_bonus: 所有固定生命值加成的总和。

    Returns:
        计算出的总生命值。
    """
    total_hp = (char_base_hp + lc_base_hp) * (1 + hp_percent_bonus) + flat_hp_bonus
    return total_hp

def calculate_total_def(char_base_def: float, lc_base_def: float, def_percent_bonus: float, flat_def_bonus: float) -> float:
    """
    计算角色的总防御力 (DEF)。

    公式: 总防御力 = (角色基础防御力 + 光锥基础防御力) * (1 + 防御力百分比加成) + 防御力固定值加成

    Args:
        char_base_def: 角色的基础防御力。
        lc_base_def: 光锥的基础防御力。
        def_percent_bonus: 所有百分比防御力加成的总和 (例如, 0.48 代表 48%)。
        flat_def_bonus: 所有固定防御力加成的总和。

    Returns:
        计算出的总防御力值。
    """
    total_def = (char_base_def + lc_base_def) * (1 + def_percent_bonus) + flat_def_bonus
    return total_def

def get_float_input(prompt: str, default: float = None) -> float:
    while True:
        try:
            user_input = input(prompt)
            if default is not None and not user_input:
                return default
            return float(user_input)
        except ValueError:
            print("Invalid input. Please enter a number.")

def get_int_input(prompt: str, default: int = None) -> int:
    while True:
        try:
            user_input = input(prompt)
            if default is not None and not user_input:
                return default
            return int(user_input)
        except ValueError:
            print("Invalid input. Please enter an integer.")

def get_list_float_input(prompt: str, default_str: str = "0.1") -> List[float]:
    while True:
        try:
            user_input = input(prompt)
            if not user_input and default_str is not None:
                user_input = default_str
            
            if not user_input: # 处理 default_str 为 None 或空字符串的情况
                 return []

            return [float(item.strip()) for item in user_input.split(',')]
        except ValueError:
            print("Invalid input. Please enter a comma-separated list of numbers (e.g., 0.1,0.05).")

def run_prydwen_examples():
    """
    根据 Prydwen.gg 文章运行示例伤害计算并断言结果。
    """
    print("\n" + "="*30)
    print("Running Prydwen.gg Examples") # CLI output, kept in English
    print("="*30)
    tolerance = 1.0 # 允许微小的四舍五入差异

    # 停云50级 vs 敌人50级通用参数 (推导出的敌人最终防御 = 700)
    tingyun_attacker_level = 50
    tingyun_atk = 1062
    tingyun_skill_multiplier = 0.6
    tingyun_lightning_dmg_bonus = 0.258
    tingyun_basic_dmg_bonus_musketeer = 0.1 # 其他伤害加成百分比
    
    enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent = 700.0

    # --- 停云示例1：敌人未破韧，非雷属性弱点 ---
    # 预期伤害：312
    print("\n--- Tingyun Example 1: Enemy not broken, not weak to Lightning ---") # CLI output
    ty_ex1_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=tingyun_skill_multiplier,
        scaling_attribute_value=tingyun_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=tingyun_lightning_dmg_bonus,
        all_type_dmg_bonus_percent=0.0,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=tingyun_basic_dmg_bonus_musketeer,
        attacker_level=tingyun_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.2, # 结果为 80% 抗性乘数
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # 90% 韧性乘数
        weaken_percent=0.0,
    )
    ty_ex1_expected_dmg = 312
    print(f"Calculated Damage: {ty_ex1_calculated_dmg:.2f}") # CLI output
    print(f"Expected Damage: {ty_ex1_expected_dmg}") # CLI output
    if abs(ty_ex1_calculated_dmg - ty_ex1_expected_dmg) < tolerance:
        print("Test Passed") # CLI output
    else:
        print(f"Test Failed. Difference: {abs(ty_ex1_calculated_dmg - ty_ex1_expected_dmg):.2f}") # CLI output

    # --- 停云示例2：敌人已破韧 ---
    # 预期伤害：346
    print("\n--- Tingyun Example 2: Enemy broken ---") # CLI output
    ty_ex2_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=tingyun_skill_multiplier,
        scaling_attribute_value=tingyun_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=tingyun_lightning_dmg_bonus,
        all_type_dmg_bonus_percent=0.0,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=tingyun_basic_dmg_bonus_musketeer,
        attacker_level=tingyun_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.2, # 非雷属性弱点
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[], # 已破韧，所以 100% 韧性乘数
        weaken_percent=0.0,
    )
    ty_ex2_expected_dmg = 346
    print(f"Calculated Damage: {ty_ex2_calculated_dmg:.2f}") # CLI output
    print(f"Expected Damage: {ty_ex2_expected_dmg}") # CLI output
    if abs(ty_ex2_calculated_dmg - ty_ex2_expected_dmg) < tolerance:
        print("Test Passed") # CLI output
    else:
        print(f"Test Failed. Difference: {abs(ty_ex2_calculated_dmg - ty_ex2_expected_dmg):.2f}") # CLI output

    # --- 停云示例3：敌人雷属性弱点，未破韧 ---
    # 预期伤害：389
    print("\n--- Tingyun Example 3: Enemy weak to Lightning, not broken ---") # CLI output
    ty_ex3_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=tingyun_skill_multiplier,
        scaling_attribute_value=tingyun_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=tingyun_lightning_dmg_bonus,
        all_type_dmg_bonus_percent=0.0,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=tingyun_basic_dmg_bonus_musketeer,
        attacker_level=tingyun_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.0, # 雷属性弱点，100% 抗性乘数
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # 未破韧
        weaken_percent=0.0,
    )
    ty_ex3_expected_dmg = 389
    print(f"Calculated Damage: {ty_ex3_calculated_dmg:.2f}") # CLI output
    print(f"Expected Damage: {ty_ex3_expected_dmg}") # CLI output
    # Prydwen 的结果是 389.4，所以 math.isclose 在这里更好，或者使用稍高的容差
    if math.isclose(ty_ex3_calculated_dmg, ty_ex3_expected_dmg, abs_tol=tolerance):
        print("Test Passed") # CLI output
    else:
        print(f"Test Failed. Difference: {abs(ty_ex3_calculated_dmg - ty_ex3_expected_dmg):.2f}") # CLI output


    # 青雀50级 vs 敌人50级通用参数 (推导出的敌人最终防御 = 700)
    qingque_attacker_level = 50
    qingque_atk = 1432
    qingque_skill_multiplier = 0.7
    qingque_quantum_dmg_bonus = 0.186
    qingque_last_tile_buff = 0.15 # 全类型伤害加成百分比
    qingque_basic_dmg_bonus_musketeer = 0.1 # 其他伤害加成百分比

    # --- 青雀示例1：敌人未破韧，非量子属性弱点 ---
    # 预期伤害：518
    print("\n--- Qingque Example 1: Enemy not broken, not weak to Quantum ---") # CLI output
    qq_ex1_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=qingque_skill_multiplier,
        scaling_attribute_value=qingque_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=qingque_quantum_dmg_bonus,
        all_type_dmg_bonus_percent=qingque_last_tile_buff,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=qingque_basic_dmg_bonus_musketeer,
        attacker_level=qingque_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.2, # 非量子属性弱点
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # 未破韧
        weaken_percent=0.0,
    )
    qq_ex1_expected_dmg = 518
    print(f"Calculated Damage: {qq_ex1_calculated_dmg:.2f}") # CLI output
    print(f"Expected Damage: {qq_ex1_expected_dmg}") # CLI output
    if abs(qq_ex1_calculated_dmg - qq_ex1_expected_dmg) < tolerance:
        print("Test Passed") # CLI output
    else:
        print(f"Test Failed. Difference: {abs(qq_ex1_calculated_dmg - qq_ex1_expected_dmg):.2f}") # CLI output

    # --- 青雀示例2：敌人量子属性弱点，未破韧 ---
    # 预期伤害：648 (Prydwen 结果为 647.8)
    print("\n--- Qingque Example 2: Enemy weak to Quantum, not broken ---") # CLI output
    qq_ex2_calculated_dmg = calculate_outgoing_damage(
        skill_multiplier=qingque_skill_multiplier,
        scaling_attribute_value=qingque_atk,
        extra_multiplier=0.0,
        extra_dmg=0.0,
        elemental_dmg_bonus_percent=qingque_quantum_dmg_bonus,
        all_type_dmg_bonus_percent=qingque_last_tile_buff,
        dot_dmg_bonus_percent=0.0,
        other_dmg_bonus_percent=qingque_basic_dmg_bonus_musketeer,
        attacker_level=qingque_attacker_level,
        enemy_base_def=enemy_base_def_lvl50_vs_lvl50_eff_def_mult_50_percent,
        enemy_def_percent_buffs_debuffs=0.0,
        def_reduction_percent=0.0,
        def_ignore_percent=0.0,
        enemy_current_res_percent=0.0, # 量子属性弱点
        res_pen_percent=0.0,
        elemental_dmg_taken_bonus_percent=0.0,
        all_type_dmg_taken_bonus_percent=0.0,
        universal_dmg_reduction_sources=[0.1], # 未破韧
        weaken_percent=0.0,
    )
    qq_ex2_expected_dmg = 648 # Prydwen 647.8
    print(f"Calculated Damage: {qq_ex2_calculated_dmg:.2f}") # CLI output
    print(f"Expected Damage: {qq_ex2_expected_dmg} (Prydwen: 647.8)") # CLI output
    if math.isclose(qq_ex2_calculated_dmg, qq_ex2_expected_dmg, abs_tol=tolerance):
        print("Test Passed") # CLI output
    else:
        print(f"Test Failed. Difference: {abs(qq_ex2_calculated_dmg - qq_ex2_expected_dmg):.2f}") # CLI output
    
    print("\n" + "="*30)
    print("Prydwen Examples Complete") # CLI output
    print("="*30 + "\n")


if __name__ == "__main__":
    print("Welcome to the Damage Calculator CLI!") # CLI output, kept in English
    
    scaling_attribute_value = 0.0

    # 1. 可选的属性计算
    # 检查 sys.stdin.isatty() 以判断是否为交互式会话
    import sys
    run_cli_interaction = True
    if not sys.stdin.isatty(): # 如果不是交互式的 (例如通过管道输入或直接运行脚本)
        # 检查是否传递了任何命令行参数以可能绕过CLI
        # 目前，我们假设如果不是交互式的，可能会跳过直接的CLI交互
        # 或者有一个特定的标志来运行测试。对于此设置，我们假设
        # 如果不是交互式的，它可能是一个测试运行器，所以不提示。
        # 然而，当前请求是在CLI之后运行示例。
        # 一个简单的方法是检查是否有任何参数；如果 "test" 是一个参数，则跳过CLI。
        if "test" in sys.argv or "run_examples" in sys.argv:
             print("Test mode detected, skipping interactive CLI.") # CLI output
             run_cli_interaction = False
    
    if run_cli_interaction:
        calculate_stat_first_choice = input("Do you want to calculate a character's ATK, HP, or DEF first? (yes/no, default: no): ").strip().lower() # CLI input prompt
        if calculate_stat_first_choice == 'yes':
            stat_type_choice = ""
            while stat_type_choice not in ['atk', 'hp', 'def']:
                stat_type_choice = input("Which stat do you want to calculate? (atk/hp/def): ").strip().lower() # CLI input prompt
                if stat_type_choice not in ['atk', 'hp', 'def']:
                    print("Invalid stat type. Please choose 'atk', 'hp', or 'def'.") # CLI output

            char_base_stat = get_float_input(f"Enter Character Base {stat_type_choice.upper()}: ") # CLI input prompt
            lc_base_stat = get_float_input(f"Enter Light Cone Base {stat_type_choice.upper()}: ") # CLI input prompt
            stat_percent_bonus = get_float_input(f"Enter Total {stat_type_choice.upper()} Percent Bonus (e.g., 0.48 for 48%): ") # CLI input prompt
            flat_stat_bonus = get_float_input(f"Enter Total Flat {stat_type_choice.upper()} Bonus: ") # CLI input prompt

            if stat_type_choice == 'atk':
                scaling_attribute_value = calculate_total_atk(char_base_stat, lc_base_stat, stat_percent_bonus, flat_stat_bonus)
            elif stat_type_choice == 'hp':
                scaling_attribute_value = calculate_total_hp(char_base_stat, lc_base_stat, stat_percent_bonus, flat_stat_bonus)
            elif stat_type_choice == 'def':
                scaling_attribute_value = calculate_total_def(char_base_stat, lc_base_stat, stat_percent_bonus, flat_stat_bonus)
            
            print(f"Calculated Total {stat_type_choice.upper()}: {scaling_attribute_value:.2f}") # CLI output
            print("-" * 30) # CLI output

        # 2. 伤害计算输入
        print("\nEnter parameters for Outgoing Damage Calculation:") # CLI output

        if scaling_attribute_value == 0.0: # 如果上面没有计算
            scaling_attribute_value = get_float_input("Enter Scaling Attribute Value (ATK, HP, or DEF): ") # CLI input prompt
        
        skill_multiplier = get_float_input("Enter Skill Multiplier (e.g., 0.6 for 60%): ") # CLI input prompt
        extra_multiplier = get_float_input("Enter Extra Multiplier (e.g., 0.2 for 20%, default: 0): ", 0.0) # CLI input prompt
        extra_dmg = get_float_input("Enter Flat Extra Damage (default: 0): ", 0.0) # CLI input prompt
        elemental_dmg_bonus_percent = get_float_input("Enter Elemental DMG Bonus Percent (e.g., 0.389 for 38.9%): ") # CLI input prompt
        all_type_dmg_bonus_percent = get_float_input("Enter All-Type DMG Bonus Percent (default: 0): ", 0.0) # CLI input prompt
        dot_dmg_bonus_percent = get_float_input("Enter DoT DMG Bonus Percent (default: 0): ", 0.0) # CLI input prompt
        other_dmg_bonus_percent = get_float_input("Enter Other DMG Bonus Percent (e.g., Basic ATK Bonus, default: 0): ", 0.0) # CLI input prompt
        
        attacker_level = get_int_input("Enter Attacker Level: ") # CLI input prompt
        enemy_base_def = get_float_input("Enter Enemy Base DEF: ") # CLI input prompt
        enemy_def_percent_buffs_debuffs = get_float_input("Enter Enemy DEF Percent Buffs/Debuffs (e.g., 0.2 for buff, -0.1 for debuff, default: 0): ", 0.0) # CLI input prompt
        def_reduction_percent = get_float_input("Enter DEF Reduction Percent (e.g., Pela ult, default: 0): ", 0.0) # CLI input prompt
        def_ignore_percent = get_float_input("Enter DEF Ignore Percent (e.g., Seele E2, default: 0): ", 0.0) # CLI input prompt
        
        enemy_current_res_percent = get_float_input("Enter Enemy Current RES Percent (e.g., 0.2 for neutral, 0 for weakness, 0.4 for resistance): ") # CLI input prompt
        res_pen_percent = get_float_input("Enter RES Penetration Percent (default: 0): ", 0.0) # CLI input prompt
        
        elemental_dmg_taken_bonus_percent = get_float_input("Enter Elemental DMG Taken Bonus Percent (e.g., Welt ult, default: 0): ", 0.0) # CLI input prompt
        all_type_dmg_taken_bonus_percent = get_float_input("Enter All-Type DMG Taken Bonus Percent (default: 0): ", 0.0) # CLI input prompt
        
        universal_dmg_reduction_sources_str = "0.1" # 敌人韧性的默认值
        universal_dmg_reduction_sources = get_list_float_input(
            f"Enter Universal DMG Reduction Sources (comma-separated floats, e.g., '0.1,0.05', default: '{universal_dmg_reduction_sources_str}' for enemy toughness): ", # CLI input prompt
            default_str=universal_dmg_reduction_sources_str
        )

        weaken_percent = get_float_input("Enter Weaken Percent (e.g., 0.15 for 15%, default: 0): ", 0.0) # CLI input prompt

        # 3. 执行计算并显示输出
        final_damage = calculate_outgoing_damage(
            skill_multiplier=skill_multiplier,
            scaling_attribute_value=scaling_attribute_value,
            extra_multiplier=extra_multiplier,
            extra_dmg=extra_dmg,
            elemental_dmg_bonus_percent=elemental_dmg_bonus_percent,
            all_type_dmg_bonus_percent=all_type_dmg_bonus_percent,
            dot_dmg_bonus_percent=dot_dmg_bonus_percent,
            other_dmg_bonus_percent=other_dmg_bonus_percent,
            attacker_level=attacker_level,
            enemy_base_def=enemy_base_def,
            enemy_def_percent_buffs_debuffs=enemy_def_percent_buffs_debuffs,
            def_reduction_percent=def_reduction_percent,
            def_ignore_percent=def_ignore_percent,
            enemy_current_res_percent=enemy_current_res_percent,
            res_pen_percent=res_pen_percent,
            elemental_dmg_taken_bonus_percent=elemental_dmg_taken_bonus_percent,
            all_type_dmg_taken_bonus_percent=all_type_dmg_taken_bonus_percent,
            universal_dmg_reduction_sources=universal_dmg_reduction_sources,
            weaken_percent=weaken_percent,
        )

        print("-" * 30) # CLI output
        print(f"Calculated Outgoing Damage: {final_damage:.2f}") # CLI output
        print("-" * 30) # CLI output
        print("Thank you for using the Damage Calculator!") # CLI output
    
    # 总是在CLI交互（如有）后运行Prydwen示例
    run_prydwen_examples()
