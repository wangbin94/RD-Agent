# Custom Strategy Research Components

This directory contains custom components for integrating RD-Agent with the quant-strategy-lab framework.

## Components

1. `quant_strategy_lab_scenario.py`: Defines the research scenario for quant-strategy-lab
2. `quant_strategy_lab_task.py`: Represents a strategy hypothesis task
3. `quant_strategy_lab_experiment.py`: Encapsulates a strategy experiment
4. `quant_strategy_lab_coder.py`: Generates strategy code from tasks
5. `quant_strategy_lab_runner.py`: Executes strategies using quant-strategy-lab
6. `quant_strategy_lab_conf.py`: Configuration for the custom strategy research loop
7. `quant_strategy_lab_loop.py`: Main loop script for running the research

## Usage

To run the custom strategy research loop:

```bash
cd /home/wang/dl/RD-Agent
python -m rdagent.app.quant_strategy_lab_loop --data_path /path/to/data --framework vectorbt
```

## Implementation Status

The following components have been implemented:
- [x] CustomStrategyScenario
- [x] StrategyTask
- [x] StrategyExperiment
- [x] CustomStrategyCoder
- [x] CustomStrategyRunner
- [x] CustomStrategyPropSetting
- [x] Main loop script

## Next Steps

- Test the integration with a simple experiment
- Implement hypothesis generation and feedback components
- Add support for multiple strategies in a single experiment
- Improve error handling and logging