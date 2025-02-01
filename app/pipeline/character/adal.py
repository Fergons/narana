"""AdalComponent for character identification pipeline"""
from typing import Dict, Any, Tuple, Callable, Optional
from dataclasses import dataclass

from adalflow import AdalComponent, ModelClient, Parameter, GeneratorOutput, Generator

from adalflow.optim import EvalFnToTextLoss
from adalflow.core.string_parser import FloatParser

from app.pipeline.character.identification import CharacterIdentificationOutput

from adalflow.core.types import Document



@dataclass
class CharacterIdentificationSample:
    """Sample for character identification task"""
    document: Document
    id: str
    ground_truth_characters: Dict[str, str]  # name -> description

class CharacterIdentificationAdal(AdalComponent):
    """AdalComponent for character identification pipeline"""
    
    def __init__(
        self,
        model_client: ModelClient,
        model_kwargs: Dict,
        text_splitter_config: Dict,
        teacher_model_config: Dict,
        backward_engine_model_config: Dict,
        text_optimizer_model_config: Dict,
    ):
        # Initialize task
        task = CharacterIdentificationOutput(
            model_client=model_client,
            model_kwargs=model_kwargs,
            text_splitter_config=text_splitter_config
        )
        

        # Create LLM judge for evaluation
        judge = Generator(
            model_client=model_client,
            model_kwargs=model_kwargs,
            template="""
            <SYS>You are an expert literary critic evaluating character identification accuracy.
            Compare the predicted character list against the ground truth characters.
            
            Evaluation criteria:
            1. Character Coverage - Were all important characters identified? (60% of score)
            2. Description Accuracy - How well do the descriptions match? (40% of score)
            
            Output a score from 0.0 to 1.0 and brief explanation.
            </SYS>
            
            <GROUND_TRUTH>
            Characters: {{ground_truth}}
            </GROUND_TRUTH>
            
            <PREDICTION>
            Identified Characters: {{prediction}}
            </PREDICTION>
            
            <USER>Score this character identification (0.0-1.0):</USER>
            """,
            # adalflow regular expression parser
            output_processors=FloatParser
        )
        

        def llm_eval(y: GeneratorOutput, y_gt: Dict[str, str]) -> float:
            """Evaluate using LLM as judge"""
            if not y or not y_gt:
                return 0.0
            
            # Format predictions
            pred_chars = {}
            if y.data and y.data.characters:
                for char in y.data.characters:
                    pred_chars[char.name] = char.description
                
            # Format for judge
            pred_str = "\n".join([f"{name}: {desc}" for name, desc in pred_chars.items()])
            gt_str = "\n".join([f"{name}: {desc}" for name, desc in y_gt.items()])
            
            # Get judge's evaluation
            score = judge(
                prompt_kwargs={
                    "prediction": pred_str,
                    "ground_truth": gt_str
                }
            )
            
            try:
                return float(score.strip())
            except (ValueError, AttributeError):
                return 0.0
        
        # Create loss function
        loss_fn = EvalFnToTextLoss(
            eval_fn=llm_eval,
            eval_fn_desc="Character identification accuracy evaluated by LLM judge"
        )
        
        super().__init__(
            task=task,
            eval_fn=llm_eval,
            loss_fn=loss_fn,
            backward_engine_model_config=backward_engine_model_config,
            text_optimizer_model_config=text_optimizer_model_config,
            teacher_model_config=teacher_model_config,
        )

    def prepare_task(
        self, 
        sample: CharacterIdentificationSample
    ) -> Tuple[Callable, Dict]:
        """Prepare task call and kwargs for a sample"""
        print(sample)
        return self.task.call, {
            "document": sample.document,
            "id": sample.id
        }

    def prepare_eval(
        self,
        sample: CharacterIdentificationSample,
        y_pred: GeneratorOutput
    ) -> Tuple[Callable, Dict]:
        """Prepare evaluation call and kwargs"""
        pred_chars = {}
        if y_pred and y_pred.data is not None:
            for char in y_pred.data.characters:
                pred_chars[char.name] = char.description
                
        return self.eval_fn, {
            "y": pred_chars,
            "y_gt": sample.ground_truth_characters
        }

    def prepare_loss(
        self,
        sample: CharacterIdentificationSample,
        y_pred: Parameter,
        *args,
        **kwargs
    ) -> Tuple[Callable, Dict]:
        """Prepare loss call and kwargs"""
        # Extract predicted characters
        pred_chars = {}
        if y_pred.full_response and y_pred.full_response.data:
            for char in y_pred.full_response.data.characters:
                pred_chars[char.name] = char.description
                
        y_pred.eval_input = pred_chars
        
        # Create ground truth parameter
        y_gt = Parameter(
            name="y_gt",
            data=sample.ground_truth_characters,
            eval_input=sample.ground_truth_characters,
            requires_opt=False,
        )
        
        return self.loss_fn, {"kwargs": {"y": y_pred, "y_gt": y_gt}} 