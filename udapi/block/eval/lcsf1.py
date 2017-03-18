"""Block eval.LcsF1 for evaluating differences between sentences with P/R/F1."""
from udapi.core.basewriter import BaseWriter

class LcsF1(BaseWriter):
    """Evaluate differences between sentences (in different zones) with P/R/F1."""

    def __init__(self, gold_zone, attributes='form', focus='.*', details=4, **kwargs):
        """Create the LcsF1 block object."""
        super().__init__(**kwargs)
        self.gold_zone = gold_zone
        self.attributes = attributes
        self.focus = focus
        self.details = details
        self._stats = {}
        self.correct, self.pred, self.gold = 0, 0, 0

    def process_tree(self, tree):
        gold_tree = tree.bundle.get_tree(self.gold_zone)
        if tree == gold_tree:
            return
        #self._stats['zones'][tree.zone] += 1

        attrs = self.attributes.split(',')
        pred_tokens = ['_'.join(n.get_attrs(attrs)) for n in tree.descendants]
        gold_tokens = ['_'.join(n.get_attrs(attrs)) for n in gold_tree.descendants]
        common = find_lcs(pred_tokens, gold_tokens)

        # my $focus = $self->focus;
        # if ($focus ne '.*') {
        #     @common      = grep {/$focus/} @common;
        #     @pred_tokens = grep {/$focus/} @pred_tokens;
        #     @gold_tokens = grep {/$focus/} @gold_tokens;
        # }

        self.correct += len(common)
        self.pred += len(pred_tokens)
        self.gold += len(gold_tokens)

        # if ($self->details){
        #     $self->_stats->{C}{$_}++ for (@common);
        #     $self->_stats->{P}{$_}++ for (@pred_tokens);
        #     $self->_stats->{G}{$_}++ for (@gold_tokens);
        #     $self->_stats->{T}{$_}++ for (@gold_tokens, @pred_tokens);
        # }

    def process_end(self):
        # Redirect the default filehandle to the file specified by self.files
        self.before_process_document(None)

        # my %pred_zones = %{$self->_stats->{zones}};
        # my @pz = keys %pred_zones;
        # if (!@pz) {
        #     warn 'Block Eval::LcsF1 was not applied to any zone. Check the parameter zones='.$self->zones;
        # } elsif (@pz > 1){
        #     warn "Block Eval::LcsF1 was applied to more than one zone (@pz). "
        #        . 'The results are mixed together. Check the parameter zones='.$self->zones;
        # }
        # say "Comparing predicted trees (zone=@pz) with gold trees (zone="
        #     . $self->gold_zone . "), sentences=$pred_zones{$pz[0]}";
        #
        # if ($self->details){
        #     say '=== Details ===';
        #     my $total_count = $self->_stats->{T};
        #     my @tokens = sort {$total_count->{$b} <=> $total_count->{$a}} keys %{$total_count};
        #     splice @tokens, $self->details;
        #     printf "%-10s %5s %5s %5s %6s  %6s  %6s\n", qw(token pred gold corr prec rec F1);
        #     foreach my $token (@tokens){
        #         my ($p, $g, $c) = map {$self->_stats->{$_}{$token}||0} (qw(P G C));
        #         my $pr = $c / ($p || 1);
        #         my $re = $c / ($g || 1);
        #         my $f  = 2 * $pr * $re / (($pr + $re)||1);
        #         printf "%-10s %5d %5d %5d %6.2f%% %6.2f%% %6.2f%%\n",
        #             $token, $p, $g, $c, 100*$pr, 100*$re, 100*$f
        #     }
        #     say '=== Totals ==='
        # }


        print("%-9s = %7d\n"*3 % ('predicted', self.pred, 'gold', self.gold, 'correct', self.correct))
        # ($pred, $gold) = map {$_||1} ($pred, $gold); # prevent division by zero
        # my $prec = $correct / $pred;
        # my $rec  = $correct / $gold;
        # my $f1   = 2 * $prec * $rec / (($prec + $rec)||1);
        # printf "%-9s = %6.2f%%\n"x3, precision=>100*$prec, recall=>100*$rec, F1=>100*$f1;


# difflib.SequenceMatcher does not compute LCS, so let's implement it here
# TODO: make faster by trimming common prefix and sufix
def find_lcs(x, y):
    m, n = len(x), len(y)
    C = [[0] * (n + 1) for _ in range(m + 1)]
    for i in range(1, m+1):
        for j in range(1, n+1):
            C[i][j] = C[i-1][j-1] + 1 if x[i-1] == y[j-1] else max(C[i][j-1], C[i-1][j])
    index = C[m][n]
    lcs = [None] * index
    while m > 0 and n > 0:
        if x[m-1] == y[n-1]:
            lcs[index-1] = x[m-1]
            m, n, index = m-1, n-1, index-1
        elif C[m-1][n] > C[m][n-1]:
            m -= 1
        else:
            n -= 1
    return lcs


'''
Udapi::Block::Eval::LcsF1 - evaluate differences between sentences with P/R/F1

=head1 SYNOPSIS

 Eval::LcsF1 zones=en_pred gold_zone=en_gold to=results.txt

 # prints something like
 predicted =     210
 gold      =     213
 correct   =     210
 precision = 100.00%
 recall    =  98.59%
 F1        =  99.29%

 Eval::LcsF1 gold_zone=y attributes=form,upos focus='^(?i:an?|the)_DET$' details=4

 # prints something like
 === Details ===
 token       pred  gold  corr   prec     rec      F1
 the_DET      711   213   188  26.44%  88.26%  40.69%
 The_DET       82    25    19  23.17%  76.00%  35.51%
 a_DET          0    62     0   0.00%   0.00%   0.00%
 an_DET         0    16     0   0.00%   0.00%   0.00%
 === Totals ===
 predicted =     793
 gold      =     319
 correct   =     207
 precision =  26.10%
 recall    =  64.89%
 F1        =  37.23%

=head1 DESCRIPTION

This block finds differences between nodes of trees in two zones
and reports the overall precision, recall and F1.
The two zones are "predicted" (on which this block is applied)
and "gold" (which needs to be specified with parameter C<gold>).

This block also reports the number of total nodes in the predicted zone
and in the gold zone and the number of "correct" nodes,
that is predicted nodes which are also in the gold zone.
By default two nodes are considered "the same" if they have the same C<form>,
but it is possible to check also for other nodes' attributes
(with parameter C<attributes>).

As usual:

 precision = correct / predicted
 recall = correct / gold
 F1 = 2 * precision * recall / (precision + recall)

The implementation is based on finding the longest common subsequence (LCS)
between the nodes in the two trees.
This means that the two zones do not need to be explicitly word-aligned.

=head1 PARAMETERS

=head2 zones

Which zone contains the "predicted" trees?
Make sure that you specify just one zone.
If you leave the default value "all" and the document contains more zones,
the results will be mixed, which is most likely not what you wanted.
Exception: If the document conaints just two zones (predicted and gold trees),
you can keep the default value "all" because this block
will skip comparison of the gold zone with itself.

=head2 gold_zone

Which zone contains the gold-standard trees?

=head2 attributes

comma separated list of attributes which should be checked
when deciding whether two nodes are equivalent in LCS

=head2 focus

Regular expresion constraining the tokens we are interested in.
If more attributes were specified in the C<attributes> parameter,
their values are concatenated with underscore, so C<focus> should reflect that
e.g. C<attributes=form,upos focus='^(a|the)_DET$'>.

For case-insensitive focus use e.g. C<focus='^(?i)the$'>
(which is equivalent to C<focus='^[Tt][Hh][Ee]$'>)

=head2 details

Print also detailed statistics for each token (matching the C<focus>).
The value of this parameter C<details> specifies the number of tokens to include.
The tokens are sorted according to the sum of their I<predicted> and I<gold> counts.

'''
