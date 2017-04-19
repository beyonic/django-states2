from __future__ import absolute_import
import logging
import os
from optparse import make_option
import pygraphviz as gvz

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.apps import apps
import six

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    def add_arguments(self, parser):
        #Positionnal arguments
        parser.add_argument('model_label', nargs='+', \
         help='model name, i.e. mvno.subscription.state')

        # Named (optional) arguments
        parser.add_argument(
            '--layout',
            '-l',
            action='store',
            dest='layout',
            default='dot',
            help='Layout to be used by GraphViz for visualization. Layouts: circo dot fdp neato twopi')

        parser.add_argument(
            '--format',
            '-f',
            action='store',
            dest='format',
            default='pdf',
            help='Format of the output file. Formats: pdf, jpg, png')

        parser.add_argument(
            '--create-dot',
            action='store_true',
            dest='create_dot',
            default=False,
            help='Create a dot file')


    def handle(self, *args, **options):
        model_label_args = options.pop('model_label')
        if len(model_label_args) < 1:
            raise CommandError('need one or more arguments for model_name.field')

        for model_label in model_label_args:
            self.render_for_model(model_label, **options)

    def render_for_model(self, model_label, **options):
        app_label,model,field = model_label.split('.')
        try:
            Model = apps.get_model(app_label, model)
        except LookupError:
            Model = None
        STATE_MACHINE = getattr(Model(), 'get_%s_machine' % field)()

        name = six.text_type(Model._meta.verbose_name)

        g = gvz.AGraph()
        #Graph('state_machine_graph_%s' % model_label, False)
        g.label = 'State Machine Graph %s' % name
        nodes = {}
        edges = {}

        for state in STATE_MACHINE.states:
            g.add_node(state,label=state.upper(),
                shape='rect',
                fontname='Arial')

            nodes[state] = g.get_node(state)
            logger.debug('Created node for %s', state)

        def find(f, a):
            for i in a:
                if f(i): return i
            return None

        for trion_name,trion in six.iteritems(STATE_MACHINE.transitions):
            for from_state in trion.from_states:
                g.add_edge(nodes[from_state], nodes[trion.to_state])
                edge = g.get_edge(nodes[from_state], nodes[trion.to_state])
                edge.dir = 'forward'
                edge.arrowhead = 'normal'
                edge.label = '\n_'.join(trion.get_name().split('_'))
                edge.fontsize = 8
                edge.fontname = 'Arial'

                if getattr(trion, 'confirm_needed', False):
                    edge.style = 'dotted'
                edges[u'%s-->%s' % (from_state, trion.to_state)] = edge
            logger.debug('Created %d edges for %s', len(trion.from_states), trion.get_name())

            #if trion.next_function_name is not None:
            #    tr = find(lambda t: t.function_name == trion.next_function_name and t.from_state == trion.to_state, STATE_MACHINE.trions)
            #    while tr.next_function_name is not None:
            #        tr = find(lambda t: t.function_name == tr.next_function_name and t.from_state == tr.to_state, STATE_MACHINE.trions)

            #    if tr is not None:
            #        meta_edge = g.add_edge(nodes[trion.from_state], nodes[tr.to_state])
            #        meta_edge.arrowhead = 'empty'
            #        meta_edge.label = '\n_'.join(trion.function_name.split('_')) + '\n(compound)'
            #        meta_edge.fontsize = 8
            #        meta_edge.fontname = 'Arial'
            #        meta_edge.color = 'blue'

            #if any(lambda t: (t.next_function_name == trion.function_name), STATE_MACHINE.trions):
            #    edge.color = 'red'
            #    edge.style = 'dashed'
            #    edge.label += '\n(auto)'
        logger.info('Creating state graph for %s with %d nodes and %d edges' % (name, len(nodes), len(edges)))

        loc = 'state_machine_%s' % (model_label,)
        if options['create_dot']:
            g.write('%s.dot' % loc)

        logger.debug('Setting layout %s' % options['layout'])
        g.layout(options['layout'])
        format = options['format']
        logger.debug('Trying to render %s' % loc)
        g.draw(loc + '.' + format, format=options['format'])
        logger.info('Created state graph for %s at %s' % (name, loc))
