       spans_key (str): The key where the note spans are present
            metadata_key (str): The key where the note metadata is present
            group_key (str): The key where the note group (e.g note_id or patient id etc) is present.
                             This field is what the notes will be grouped by, and all notes belonging
                             to this grouping will be in the same split
            margin (float): Margin of error when maintaining proportions in the splits
        """
        # Compute the distribution of NER types in the grouped notes.
        # For example the distribution of NER types in all notes belonging to a
        # particular patient
        self._lookup_split = {
            'train': dict(),
            'validation': dict(),
            'test': dict()
        }
        ner_distribution = NERDistribution()
        for line in open(input_file, 'r'):
            note = json.loads(line)
            key = note[metadata_key][group_key]
            ner_distribution.update_distribution(spans=note[spans_key], key=key)
        # Initialize the dataset splits object
        dataset_splits = DatasetSplits(
            ner_distribution=ner_distribution,
            train_proportion=self._train_proportion,
            validation_proportion=self._validation_proportion,
            test_proportion=self._test_proportion,
            margin=margin
        )
        # Check the note and assign it to a split
        for line in open(input_file, 'r'):
            note = json.loads(line)
            key = note[metadata_key][group_key]
            split = dataset_splits.get_split(key=key)
            self.set_split(split)
            