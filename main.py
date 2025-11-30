"""
🧬 CRISPR-FinAI — Bio-Inspired Adaptive Financial Intelligence
Main Application Orchestrator & Command Line Interface

Complete integration of all CRISPR components for end-to-end
financial model optimization with biological precision.

From genome to phenotype. From data to insights.
Every edit matters. Every optimization counts.
"""

import argparse
import logging
import sys
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import warnings

# Core CRISPR components
from src.core.genome import FinancialGenome
from src.data.loader import FinancialDataLoader
from src.detector.isolation_detector import IsolationDetector
from src.guide.guide_agent import AttentionGuide
from src.editor.ga_editor import GeneticAlgorithmEditor
from src.repair.stabilizer import CellularRepair, RepairConfig
from src.audit.compliance import ComprehensiveAudit, AuditConfig
from src.evaluation.evaluator import CRISPREvaluator, BacktestConfig

# Configuration
warnings.filterwarnings('ignore')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class CRISPRFinAI:
    """
    🧬 Main CRISPR-FinAI System Orchestrator
    
    Central command center for bio-inspired financial model optimization.
    Coordinates all CRISPR components in a unified workflow.
    
    Biological Analogy:
    - Cell Nucleus → System Orchestrator
    - DNA → Financial Model Parameters
    - Proteins → Trading Strategies
    - Metabolism → Performance Optimization
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize CRISPR-FinAI system with all biological layers.
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.session_id = f"crispr_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Initialize core components
        self._initialize_components()

        # System state
        self.active_genomes: Dict[str, FinancialGenome] = {}
        self.session_results = {
            'session_id': self.session_id,
            'start_time': datetime.now(),
            'operations_performed': [],
            'total_edits': 0,
            'total_detections': 0,
            'total_repairs': 0,
            'performance_metrics': {}
        }

        logger.info(f"🧬 CRISPR-FinAI initialized - Session: {self.session_id}")

    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load system configuration."""
        default_config = {
            'data': {
                'symbols': ['AAPL', 'GOOGL', 'MSFT', 'AMZN'],
                'start_date': '2020-01-01',
                'end_date': '2023-12-31',
                'data_source': 'yahoo'
            },
            'detection': {
                'contamination': 0.1,
                'n_estimators': 100,
                'max_samples': 256,
                'enable_statistical_drift': True,
                'drift_window_size': 50
            },
            'editing': {
                'population_size': 50,
                'max_generations': 100,
                'mutation_rate': 0.1,
                'crossover_rate': 0.8,
                'elite_size': 5
            },
            'repair': {
                'stability_threshold': 0.8,
                'gradient_clip_threshold': 1.0,
                'regularization_strength': 0.01,
                'emergency_threshold': 0.3
            },
            'audit': {
                'max_audit_entries': 10000,
                'audit_retention_days': 365,
                'enable_real_time_monitoring': True,
                'enable_blockchain_audit': False
            },
            'evaluation': {
                'initial_capital': 100000.0,
                'transaction_costs': 0.001,
                'max_position_size': 0.1,
                'benchmark_symbols': ['SPY', 'QQQ']
            }
        }

        if config_path and Path(config_path).exists():
            try:
                with open(config_path) as f:
                    user_config = json.load(f)

                # Merge configurations
                for section, settings in user_config.items():
                    if section in default_config:
                        default_config[section].update(settings)
                    else:
                        default_config[section] = settings

                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.warning(f"Failed to load config from {config_path}: {str(e)}")
                logger.info("Using default configuration")

        return default_config

    def _initialize_components(self):
        """Initialize all CRISPR biological layers."""
        logger.info("Initializing CRISPR biological layers...")

        # Data Layer - The Environment
        self.data_loader = FinancialDataLoader()

        # Detection Layer - Immune System
        self.detector = IsolationDetector(
            "IsolationDetector",
            contamination=self.config['detection']['contamination'],
            n_estimators=self.config['detection']['n_estimators'],
            max_samples=self.config['detection']['max_samples']
        )

        # Guide Layer - Guide RNA System
        self.guide = AttentionGuide("AttentionGuide")

        # Editor Layer - Cas Protein
        from src.editor.ga_editor import GAConfig
        editor_config = GAConfig(
            population_size=self.config['editing']['population_size'],
            max_generations=self.config['editing']['max_generations'],
            mutation_rate=self.config['editing']['mutation_rate'],
            crossover_rate=self.config['editing']['crossover_rate'],
            elite_size=self.config['editing']['elite_size']
        )
        self.editor = GeneticAlgorithmEditor("GeneticEditor", editor_config)

        # Repair Layer - DNA Repair Machinery
        repair_config = RepairConfig(
            stability_threshold=self.config['repair']['stability_threshold'],
            gradient_clip_threshold=self.config['repair']['gradient_clip_threshold'],
            regularization_strength=self.config['repair']['regularization_strength'],
            emergency_threshold=self.config['repair']['emergency_threshold']
        )
        self.repair = CellularRepair("CellularRepair", repair_config)

        # Audit Layer - Quality Control
        audit_config = AuditConfig(
            max_audit_entries=self.config['audit']['max_audit_entries'],
            audit_retention_days=self.config['audit']['audit_retention_days'],
            enable_real_time_monitoring=self.config['audit']['enable_real_time_monitoring'],
            enable_blockchain_audit=self.config['audit']['enable_blockchain_audit']
        )
        self.audit = ComprehensiveAudit("ComprehensiveAudit", audit_config)

        # Evaluation Layer - Clinical Trials
        eval_config = BacktestConfig(
            start_date=self.config['data']['start_date'],
            end_date=self.config['data']['end_date'],
            initial_capital=self.config['evaluation']['initial_capital'],
            transaction_costs=self.config['evaluation']['transaction_costs'],
            max_position_size=self.config['evaluation']['max_position_size'],
            benchmark_symbols=self.config['evaluation']['benchmark_symbols']
        )
        self.evaluator = CRISPREvaluator(eval_config, self.data_loader)

        logger.info("✅ All CRISPR components initialized successfully")

    def create_genome(self, name: str, symbol: str) -> str:
        """
        🧬 Create new financial genome for a symbol
        
        Args:
            name: Genome identifier
            symbol: Financial symbol
            
        Returns:
            Genome ID
        """
        logger.info(f"Creating financial genome: {name} for {symbol}")

        try:
            genome = FinancialGenome(name)

            # Initialize with symbol-specific parameters
            genome.add_parameter("strategy.momentum_window", 20, {"min": 5, "max": 100})
            genome.add_parameter("strategy.mean_reversion_window", 50, {"min": 10, "max": 200})
            genome.add_parameter("strategy.volatility_lookback", 30, {"min": 5, "max": 100})

            # Risk management genes
            genome.add_parameter("risk.max_position", 0.1, {"min": 0.01, "max": 0.5})
            genome.add_parameter("risk.stop_loss", -0.05, {"min": -0.2, "max": -0.01})
            genome.add_parameter("risk.volatility_target", 0.15, {"min": 0.05, "max": 0.5})

            # Technical indicators
            genome.add_parameter("indicators.rsi_period", 14, {"min": 5, "max": 50})
            genome.add_parameter("indicators.macd_fast", 12, {"min": 5, "max": 30})
            genome.add_parameter("indicators.macd_slow", 26, {"min": 20, "max": 100})

            # Store genome
            self.active_genomes[name] = genome

            # Log creation
            self.audit.log_detection({
                'event_type': 'genome_creation',
                'symbol': symbol,
                'parameters_initialized': len(genome.list_all_parameters())
            }, genome, "system")

            logger.info(f"✅ Genome {name} created with {len(genome.list_all_parameters())} parameters")

            return name

        except Exception as e:
            logger.error(f"Failed to create genome {name}: {str(e)}")
            raise

    def sequence_genome(self, genome_name: str, symbol: str) -> Dict[str, Any]:
        """
        🔍 Perform genome sequencing (anomaly detection)
        
        Args:
            genome_name: Name of genome to sequence
            symbol: Financial symbol for data
            
        Returns:
            Sequencing results
        """
        logger.info(f"Sequencing genome: {genome_name} for {symbol}")

        if genome_name not in self.active_genomes:
            raise ValueError(f"Genome {genome_name} not found")

        genome = self.active_genomes[genome_name]

        try:
            # Load financial data
            data = self.data_loader.load_symbol_data(
                symbol,
                start_date=self.config['data']['start_date'],
                end_date=self.config['data']['end_date']
            )

            if data is None or len(data) < 100:
                raise ValueError(f"Insufficient data for {symbol}")

            # Perform anomaly detection
            detection_result = self.detector.detect_anomalies(genome, data.values)

            # Log detection
            self.audit.log_detection({
                'symbol': symbol,
                'anomaly_detected': detection_result.anomaly_detected,
                'anomaly_score': detection_result.anomaly_score,
                'affected_regions': detection_result.affected_regions
            }, genome, "detector")

            self.session_results['total_detections'] += 1

            sequencing_results = {
                'genome_name': genome_name,
                'symbol': symbol,
                'anomaly_detected': detection_result.anomaly_detected,
                'anomaly_score': detection_result.anomaly_score,
                'affected_regions': detection_result.affected_regions,
                'confidence': detection_result.confidence,
                'timestamp': datetime.now()
            }

            logger.info(f"Sequencing complete: anomaly_detected={detection_result.anomaly_detected}, "
                       f"score={detection_result.anomaly_score:.3f}")

            return sequencing_results

        except Exception as e:
            logger.error(f"Genome sequencing failed: {str(e)}")
            raise

    def edit_genome(self, genome_name: str, detection_result: Dict) -> Dict[str, Any]:
        """
        ✂️ Perform CRISPR-style genome editing
        
        Args:
            genome_name: Name of genome to edit
            detection_result: Results from sequencing
            
        Returns:
            Editing results
        """
        logger.info(f"Performing CRISPR edit on genome: {genome_name}")

        if genome_name not in self.active_genomes:
            raise ValueError(f"Genome {genome_name} not found")

        genome = self.active_genomes[genome_name]

        try:
            # Convert detection result to proper format
            from src.core.base_layers import DetectionResult
            detection_obj = DetectionResult(
                anomaly_detected=detection_result['anomaly_detected'],
                anomaly_score=detection_result['anomaly_score'],
                affected_regions=detection_result['affected_regions'],
                confidence=detection_result['confidence'],
                timestamp=detection_result['timestamp']
            )

            # Guide phase - identify target sites
            target_sites = self.guide.identify_targets(genome, detection_obj)

            if not target_sites:
                logger.warning("No target sites identified for editing")
                return {
                    'success': False,
                    'reason': 'No target sites identified',
                    'target_sites': []
                }

            # Editor phase - perform genetic modifications
            edit_result = self.editor.edit_parameters(genome, target_sites)

            # Log edit
            self.audit.log_edit(edit_result, genome, "editor")

            self.session_results['total_edits'] += 1

            editing_results = {
                'genome_name': genome_name,
                'success': edit_result.success,
                'target_parameters': edit_result.target_parameters,
                'edit_strategy': edit_result.edit_strategy,
                'parameter_changes': edit_result.parameter_changes,
                'fitness_improvement': edit_result.fitness_improvement,
                'performance_delta': edit_result.performance_delta,
                'convergence_generation': getattr(edit_result, 'convergence_generation', None),
                'timestamp': datetime.now()
            }

            logger.info(f"CRISPR edit complete: success={edit_result.success}, "
                       f"targets={len(edit_result.target_parameters)}")

            return editing_results

        except Exception as e:
            logger.error(f"Genome editing failed: {str(e)}")
            raise

    def repair_genome(self, genome_name: str) -> Dict[str, Any]:
        """
        🔧 Perform cellular repair on genome
        
        Args:
            genome_name: Name of genome to repair
            
        Returns:
            Repair results
        """
        logger.info(f"Performing cellular repair on genome: {genome_name}")

        if genome_name not in self.active_genomes:
            raise ValueError(f"Genome {genome_name} not found")

        genome = self.active_genomes[genome_name]

        try:
            # Assess current stability
            stability_score = self.repair.assess_stability(genome, [])

            repair_results = {
                'genome_name': genome_name,
                'initial_stability': stability_score,
                'repair_needed': stability_score < self.repair.config.stability_threshold,
                'timestamp': datetime.now()
            }

            if repair_results['repair_needed']:
                # Identify instability sources
                instability_sources = ["parameter_drift", "constraint_violation"]

                # Perform repair
                repair_result = self.repair.repair(genome, instability_sources)

                # Log repair
                self.audit.log_repair(repair_result, genome, "repair_system")

                repair_results.update(repair_result)
                self.session_results['total_repairs'] += 1

                logger.info(f"Repair complete: success={repair_result['success']}, "
                           f"stability improvement={repair_result.get('final_stability', 0) - stability_score:.3f}")
            else:
                repair_results['success'] = True
                repair_results['message'] = "No repair needed - genome stable"
                logger.info("Genome stable - no repair needed")

            return repair_results

        except Exception as e:
            logger.error(f"Genome repair failed: {str(e)}")
            raise

    def optimize_portfolio(self, symbols: List[str], optimization_cycles: int = 5) -> Dict[str, Any]:
        """
        🎯 Full portfolio optimization using CRISPR workflow
        
        Args:
            symbols: List of symbols to optimize
            optimization_cycles: Number of optimization cycles
            
        Returns:
            Portfolio optimization results
        """
        logger.info(f"Starting portfolio optimization for {len(symbols)} symbols")

        optimization_results = {
            'symbols': symbols,
            'optimization_cycles': optimization_cycles,
            'genome_results': {},
            'portfolio_performance': {},
            'optimization_summary': {},
            'timestamp': datetime.now()
        }

        try:
            # Create genomes for each symbol
            for symbol in symbols:
                genome_name = f"{symbol}_genome"
                self.create_genome(genome_name, symbol)
                optimization_results['genome_results'][symbol] = {'genome_name': genome_name}

            # Optimization cycles
            for cycle in range(optimization_cycles):
                logger.info(f"Optimization cycle {cycle + 1}/{optimization_cycles}")

                for symbol in symbols:
                    genome_name = f"{symbol}_genome"

                    try:
                        # 1. Sequence genome (detect anomalies)
                        sequencing_result = self.sequence_genome(genome_name, symbol)

                        # 2. Edit if anomalies detected
                        if sequencing_result['anomaly_detected']:
                            editing_result = self.edit_genome(genome_name, sequencing_result)
                            optimization_results['genome_results'][symbol][f'cycle_{cycle}_edit'] = editing_result

                        # 3. Repair if needed
                        repair_result = self.repair_genome(genome_name)
                        optimization_results['genome_results'][symbol][f'cycle_{cycle}_repair'] = repair_result

                    except Exception as e:
                        logger.error(f"Failed optimization for {symbol} in cycle {cycle}: {str(e)}")
                        optimization_results['genome_results'][symbol][f'cycle_{cycle}_error'] = str(e)

            # Generate optimization summary
            optimization_results['optimization_summary'] = {
                'total_edits': self.session_results['total_edits'],
                'total_repairs': self.session_results['total_repairs'],
                'total_detections': self.session_results['total_detections'],
                'active_genomes': len(self.active_genomes),
                'session_duration': (datetime.now() - self.session_results['start_time']).total_seconds()
            }

            logger.info(f"Portfolio optimization complete: {optimization_results['optimization_summary']}")

            return optimization_results

        except Exception as e:
            logger.error(f"Portfolio optimization failed: {str(e)}")
            optimization_results['error'] = str(e)
            return optimization_results

    def run_evaluation(self, symbols: List[str]) -> Dict[str, Any]:
        """
        📊 Run comprehensive evaluation
        
        Args:
            symbols: Symbols to evaluate
            
        Returns:
            Evaluation results
        """
        logger.info(f"Running comprehensive evaluation for {len(symbols)} symbols")

        try:
            evaluation_results = self.evaluator.run_comprehensive_evaluation(symbols)

            # Store in session results
            self.session_results['performance_metrics'] = evaluation_results

            logger.info("Comprehensive evaluation completed successfully")

            return evaluation_results

        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            raise

    def generate_compliance_report(self) -> Dict[str, Any]:
        """
        📋 Generate compliance report
        
        Returns:
            Compliance report
        """
        logger.info("Generating compliance report...")

        try:
            compliance_report = self.audit.generate_compliance_report(days_back=30)

            logger.info(f"Compliance report generated: score={compliance_report.compliance_score:.3f}")

            return compliance_report.to_dict()

        except Exception as e:
            logger.error(f"Compliance report generation failed: {str(e)}")
            raise

    def get_system_status(self) -> Dict[str, Any]:
        """
        📊 Get comprehensive system status
        
        Returns:
            System status information
        """
        try:
            # Audit statistics
            audit_stats = self.audit.get_audit_statistics()

            # Repair statistics
            repair_stats = self.repair.get_repair_statistics()

            # System status
            status = {
                'session_id': self.session_id,
                'uptime_seconds': (datetime.now() - self.session_results['start_time']).total_seconds(),
                'active_genomes': len(self.active_genomes),
                'genome_list': list(self.active_genomes.keys()),
                'operations_performed': {
                    'total_edits': self.session_results['total_edits'],
                    'total_detections': self.session_results['total_detections'],
                    'total_repairs': self.session_results['total_repairs']
                },
                'component_status': {
                    'detector': 'operational',
                    'guide': 'operational',
                    'editor': 'operational',
                    'repair': 'operational',
                    'audit': 'operational'
                },
                'audit_statistics': audit_stats,
                'repair_statistics': repair_stats
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get system status: {str(e)}")
            return {'error': str(e)}

    def save_session(self, filepath: Optional[str] = None) -> str:
        """
        💾 Save current session state
        
        Args:
            filepath: Optional custom filepath
            
        Returns:
            Path where session was saved
        """
        if filepath is None:
            filepath = f"./sessions/session_{self.session_id}.json"

        Path(filepath).parent.mkdir(parents=True, exist_ok=True)

        # Prepare session data
        session_data = {
            'session_info': self.session_results,
            'config': self.config,
            'genomes': {name: genome.to_dict() for name, genome in self.active_genomes.items()},
            'system_status': self.get_system_status()
        }

        try:
            with open(filepath, 'w') as f:
                json.dump(session_data, f, indent=2, default=str)

            logger.info(f"Session saved to {filepath}")
            return filepath

        except Exception as e:
            logger.error(f"Failed to save session: {str(e)}")
            raise


def create_cli_parser() -> argparse.ArgumentParser:
    """Create command line interface parser."""
    parser = argparse.ArgumentParser(
        description="🧬 CRISPR-FinAI — Bio-Inspired Adaptive Financial Intelligence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Optimize portfolio with default symbols
  python main.py optimize --symbols AAPL GOOGL MSFT
  
  # Run evaluation with custom config
  python main.py evaluate --config config.json --symbols AAPL GOOGL
  
  # Generate compliance report
  python main.py compliance --days 30
  
  # Get system status
  python main.py status
        """
    )

    parser.add_argument(
        '--config', '-c',
        type=str,
        help='Path to configuration file'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Optimize command
    optimize_parser = subparsers.add_parser('optimize', help='Run portfolio optimization')
    optimize_parser.add_argument(
        '--symbols', '-s',
        nargs='+',
        default=['AAPL', 'GOOGL', 'MSFT', 'AMZN'],
        help='Symbols to optimize'
    )
    optimize_parser.add_argument(
        '--cycles',
        type=int,
        default=5,
        help='Number of optimization cycles'
    )

    # Evaluate command
    evaluate_parser = subparsers.add_parser('evaluate', help='Run comprehensive evaluation')
    evaluate_parser.add_argument(
        '--symbols', '-s',
        nargs='+',
        default=['AAPL', 'GOOGL', 'MSFT'],
        help='Symbols to evaluate'
    )

    # Compliance command
    compliance_parser = subparsers.add_parser('compliance', help='Generate compliance report')
    compliance_parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Number of days to include in report'
    )

    # Status command
    subparsers.add_parser('status', help='Get system status')

    # Create genome command
    genome_parser = subparsers.add_parser('create-genome', help='Create new genome')
    genome_parser.add_argument('name', help='Genome name')
    genome_parser.add_argument('symbol', help='Financial symbol')

    # Sequence command
    sequence_parser = subparsers.add_parser('sequence', help='Sequence genome')
    sequence_parser.add_argument('genome', help='Genome name')
    sequence_parser.add_argument('symbol', help='Financial symbol')

    return parser


def main():
    """Main application entry point."""
    parser = create_cli_parser()
    args = parser.parse_args()

    # Configure logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Print banner
    print("""
    🧬 CRISPR-FinAI — Bio-Inspired Adaptive Financial Intelligence
    ================================================================
    Precision editing for financial model optimization
    Where biology meets quantitative finance.
    """)

    try:
        # Initialize CRISPR system
        crispr = CRISPRFinAI(args.config)

        if args.command == 'optimize':
            print(f"🎯 Optimizing portfolio for symbols: {args.symbols}")
            results = crispr.optimize_portfolio(args.symbols, args.cycles)

            print("\\n📊 Optimization Results:")
            print(f"Total Edits: {results['optimization_summary']['total_edits']}")
            print(f"Total Repairs: {results['optimization_summary']['total_repairs']}")
            print(f"Session Duration: {results['optimization_summary']['session_duration']:.2f}s")

            # Save results
            results_file = crispr.save_session()
            print(f"📁 Results saved to: {results_file}")

        elif args.command == 'evaluate':
            print(f"📊 Running evaluation for symbols: {args.symbols}")
            results = crispr.run_evaluation(args.symbols)

            print("\\n📈 Evaluation Results:")
            crispr_metrics = results.get('results', {}).get('crispr', {}).get('metrics', {})
            if crispr_metrics:
                print(f"Sharpe Ratio: {crispr_metrics.get('sharpe_ratio', 0):.3f}")
                print(f"Annual Return: {crispr_metrics.get('annual_return', 0):.2%}")
                print(f"Edit Success Rate: {crispr_metrics.get('edit_success_rate', 0):.2%}")

        elif args.command == 'compliance':
            print(f"📋 Generating compliance report for {args.days} days")
            report = crispr.generate_compliance_report()

            print("\\n⚖️ Compliance Report:")
            print(f"Compliance Score: {report['compliance_score']:.3f}")
            print(f"Total Violations: {len(report['violations'])}")
            print(f"Emergency Activations: {report['emergency_activations']}")

        elif args.command == 'status':
            print("📊 System Status:")
            status = crispr.get_system_status()

            print(f"Session ID: {status['session_id']}")
            print(f"Uptime: {status['uptime_seconds']:.2f}s")
            print(f"Active Genomes: {status['active_genomes']}")
            print(f"Total Operations: {sum(status['operations_performed'].values())}")

        elif args.command == 'create-genome':
            print(f"🧬 Creating genome: {args.name} for {args.symbol}")
            genome_id = crispr.create_genome(args.name, args.symbol)
            print(f"✅ Genome created: {genome_id}")

        elif args.command == 'sequence':
            print(f"🔍 Sequencing genome: {args.genome} for {args.symbol}")
            results = crispr.sequence_genome(args.genome, args.symbol)

            print("\\n🧬 Sequencing Results:")
            print(f"Anomaly Detected: {results['anomaly_detected']}")
            print(f"Anomaly Score: {results['anomaly_score']:.3f}")
            print(f"Affected Regions: {len(results['affected_regions'])}")

        else:
            parser.print_help()

    except KeyboardInterrupt:
        print("\\n🛑 Operation cancelled by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {str(e)}")
        print(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == '__main__':
    main()
