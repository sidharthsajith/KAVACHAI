#!/usr/bin/env python3
"""
CLI tool for testing the Kavach AI guardrail functionality.
"""

import argparse
import json
import sys
from kavach_ai.guardrail import (
    Guardrail, 
    GuardrailConfig, 
    DEFAULT_GUARDRAIL_CONFIG, 
    JAILBREAK_PROTECTION_CONFIG,
    ContentCategory,
    ModerationLevel,
    print_moderation_result,
    print_detailed_analysis,
    analyze_content_deeply
)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Test Kavach AI guardrail functionality")
    
    # Main arguments
    parser.add_argument("--input", "-i", type=str, help="Input text to check")
    parser.add_argument("--file", "-f", type=str, help="Input file to check")
    parser.add_argument("--output", "-o", type=str, help="Output file for results (JSON format)")
    
    # Guardrail configuration
    parser.add_argument("--config", "-c", type=str, choices=["default", "jailbreak"], 
                        default="default", help="Guardrail configuration to use")
    parser.add_argument("--level", "-l", type=str, choices=["strict", "moderate", "permissive"], 
                        help="Moderation level")
    
    # Analysis options
    parser.add_argument("--deep-analysis", "-d", action="store_true", 
                        help="Perform deep analysis with multiple guardrails")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Show detailed output")
    parser.add_argument("--json", "-j", action="store_true", 
                        help="Output results in JSON format")
    parser.add_argument("--pattern-only", "-p", action="store_true",
                        help="Use only pattern matching (no LLM checks)")
    
    return parser.parse_args()

def get_input_content(args):
    """Get content from input argument or file."""
    if args.input:
        return args.input
    elif args.file:
        try:
            with open(args.file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error reading file: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Please provide input text or file", file=sys.stderr)
        sys.exit(1)

def create_guardrail_config(args):
    """Create guardrail configuration based on arguments."""
    if args.config == "default":
        config = DEFAULT_GUARDRAIL_CONFIG.model_copy()  # Using model_copy instead of copy
    else:  # jailbreak
        config = JAILBREAK_PROTECTION_CONFIG.model_copy()  # Using model_copy instead of copy
    
    # Override level if specified
    if args.level:
        config.level = ModerationLevel(args.level)
    
    # Disable LLM check if pattern-only is specified
    if args.pattern_only:
        config.enable_llm_check = False
    
    return config

def main():
    """Main function."""
    args = parse_args()
    content = get_input_content(args)
    
    # Create guardrail configuration
    config = create_guardrail_config(args)
    
    # Perform analysis
    if args.deep_analysis:
        result = analyze_content_deeply(content)
        
        if args.json or args.output:
            json_result = json.dumps(result, indent=2)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_result)
            if args.json:
                print(json_result)
            else:
                print(f"Results saved to {args.output}")
        else:
            print_detailed_analysis(result)
    else:
        # Create guardrail and check content
        guardrail = Guardrail(config)
        
        # Add the missing _create_system_prompt method to the guardrail object
        if not hasattr(guardrail, '_create_system_prompt'):
            guardrail._create_system_prompt = lambda: f"""
            You are a content moderation system. Your task is to analyze the given content and determine if it should be flagged.
            
            Guardrail Configuration:
            - Name: {config.name}
            - Description: {config.description}
            - Categories to monitor: {', '.join([cat.value for cat in config.categories])}
            - Moderation Level: {config.level.value}
            
            Please analyze the content and respond with a JSON object containing:
            - flagged: boolean (true if content should be flagged, false otherwise)
            - categories: array of strings (categories that were triggered)
            - reason: string (reason for flagging, if applicable)
            - confidence_score: number between 0 and 1
            """
        
        # Add the missing _segment_content method if needed
        if not hasattr(guardrail, '_segment_content'):
            guardrail._segment_content = lambda content: content
        
        result = guardrail.check_content(content)
        
        if args.json or args.output:
            # Convert result to dict for JSON serialization
            result_dict = {
                "content": result.content[:100] + "..." if len(result.content) > 100 else result.content,
                "flagged": result.flagged,
                "categories": [cat.value for cat in result.categories] if result.categories else [],
                "reason": result.reason,
                "confidence_score": result.confidence_score,
                "detection_method": result.detection_method,
                "processing_time": result.processing_time
            }
            
            json_result = json.dumps(result_dict, indent=2)
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(json_result)
            if args.json:
                print(json_result)
            else:
                print(f"Results saved to {args.output}")
        else:
            print_moderation_result(result)

if __name__ == "__main__":
    main()