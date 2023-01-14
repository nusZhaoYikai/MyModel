# -*- encoding:utf-8 -*-
import torch.nn as nn
from uer.layers.layer_norm import LayerNorm
from uer.layers.position_ffn import PositionwiseFeedForward
from uer.layers.multi_headed_attn import MultiHeadedAttention
from uer.layers.transformer import TransformerLayer


class BertEncoder(nn.Module):
    """
    BERT encoder exploits 12 or 24 transformer layers to extract features.
    """

    def __init__(self, args):
        super(BertEncoder, self).__init__()
        if args.use_baseline_bert:
            self.use_baseline_bert = True
            from transformers import BertModel, BertForSequenceClassification, BertConfig
            config = BertConfig.from_pretrained(args.baseline_bert_path)
            config.num_labels = args.labels_num
            self.baseline_bert = BertForSequenceClassification.from_pretrained(args.baseline_bert_path, config=config)
        else:
            self.layers_num = args.layers_num
            self.transformer = nn.ModuleList([
                TransformerLayer(args) for _ in range(self.layers_num)
            ])
            self.use_baseline_bert = False

    def forward(self, emb, seg=None, vm=None, labels=None):
        """
        Args:
            emb: [batch_size x seq_length x emb_size]
            seg: [batch_size x seq_length]
            vm: [batch_size x seq_length x seq_length]

        Returns:
            hidden: [batch_size x seq_length x hidden_size]
        """
        if self.use_baseline_bert:
            output = self.baseline_bert(emb, labels=labels)
            return output.loss, output.logits

        seq_length = emb.size(1)
        # Generate mask according to segment indicators.
        # mask: [batch_size x 1 x seq_length x seq_length]
        if vm is None:
            mask = (seg > 0). \
                unsqueeze(1). \
                repeat(1, seq_length, 1). \
                unsqueeze(1)
            mask = mask.float()
            mask = (1.0 - mask) * -10000.0
        else:
            mask = vm.unsqueeze(1)
            mask = mask.float()
            mask = (1.0 - mask) * -10000.0

        hidden = emb
        for i in range(self.layers_num):
            hidden = self.transformer[i](hidden, mask)
        return hidden  # [batch_size x seq_length x hidden_size]
