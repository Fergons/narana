from dataclasses import dataclass, field
from typing import Optional, Union
from app.utils.logging import PipelineLogger
from adalflow.core import Component, Generator, ModelClient
from adalflow import (
    DataClass,
    GeneratorOutput,
    OllamaClient,
    Parameter,
    GradComponent,
    Prompt,
)
from adalflow.optim.types import ParameterType
from adalflow.components.output_parsers import DataClassParser
from adalflow.core import Document
from adalflow.tracing import trace_generator_call, trace_generator_states
from adalflow.components.data_process.text_splitter import TextSplitter
from adalflow.core.types import Document




template = r"""<START_OF_SYSTEM_MESSAGE>
 {{system_prompt}}
 {% if output_format_str is not none %}
 {{output_format_str}}
 {% endif %}
 {% if few_shot_demos is not none %}
 Here are some examples:
 {{few_shot_demos}}
 {% endif %}
 <END_OF_SYSTEM_MESSAGE>
 <START_OF_USER_MESSAGE>
 {{input_str}}
 <END_OF_USER_MESSAGE>
 """

task_desc_template = r"""Your task is to identify the characters in the story. You will be given a snippets of a story and a list of previously identified characters from previous parts of the story.
You will need to identify the characters in the each part of the story and return the characters in a list.
<IDENTIFIED_CHARACTERS>
{{identified_characters}}
</IDENTIFIED_CHARACTERS>
<NEW_STORY_CHUNK>
{{story}}
</NEW_STORY_CHUNK>
"""


@dataclass
class Character(DataClass):
    name: str = field(metadata={"desc": "The name of the character"})
    description: str = field(metadata={"desc": "The description of the character"})

    __input_fields__ = []
    __output_fields__ = ["name", "description"]


@dataclass
class CharacterList(DataClass):
    characters: list[Character] = field(
        default_factory=list, metadata={"desc": "The list of characters in the story"}
    )

    def __str__(self):
        return "\n".join(
            [
                f"{character.name}: {character.description}"
                for character in self.characters
            ]
        )

    __input_fields__ = ["story", "identified_characters"]
    __output_fields__ = ["characters"]

@trace_generator_call()
@trace_generator_states()
class CharacterIdentificationOutput(Component):
    """
    Component for identifying characters in a story.
    """

    def __init__(self, model_client: ModelClient, model_kwargs: dict, text_splitter_config):
        super().__init__()
        self.model_client = model_client
        self.characters = {}
        self.text_splitter = TextSplitter(
            **text_splitter_config
        )


        task_desc_str = Prompt(template=task_desc_template, prompt_kwargs={})()
        self.data_class = CharacterList
        self.data_class.set_task_desc(task_desc_str)
        self.parser = DataClassParser(
            data_class=CharacterList, return_data_class=True, format_type="yaml"
        )
        prompt_kwargs = {
            "system_prompt": Parameter(
                data=self.parser.get_task_desc_str(),
                role_desc="The task is to identify the characters in the story chunk based on the previously identified characters and the new story chunk",
                requires_opt=True,
                param_type=ParameterType.PROMPT,
            ),
            "output_format_str": Parameter(
                data=self.parser.get_output_format_str(),
                role_desc="Output format requirements",
                requires_opt=False,
                param_type=ParameterType.PROMPT,
            ),
            "few_shot_demos": Parameter(
                data=None,
                requires_opt=True,
                role_desc="Few shot examples to help the model identify the characters in the story chunk",
                param_type=ParameterType.DEMOS,
            ),
        }

        self.llm = Generator(
            model_client=model_client,
            model_kwargs=model_kwargs,
            prompt_kwargs=prompt_kwargs,
            template=template,
            output_processors=self.parser,
            use_cache=True,
        )

    def _prepare_input(self, document: Document):
        # input_str = self.parser.get_input_str(input_data)
        prompt_kwargs = {
            "input_str": Parameter(
                data=document.text,
                requires_opt=False,
                role_desc="New story snippet to identify characters in.",
            )
        }
        return prompt_kwargs

    def call(
        self, document: Document, id: Optional[str] = None
    ) -> Union[GeneratorOutput, Parameter]:
        for document in self.text_splitter.call(documents=[document]):
            prompt_kwargs = self._prepare_input(document)
            output = self.llm(prompt_kwargs=prompt_kwargs, id=id)
            self.characters.update(output.data.characters)
        return self.characters


    
