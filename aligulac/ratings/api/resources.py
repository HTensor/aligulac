from urllib.request import unquote

from datetime import date
from dateutil.relativedelta import relativedelta

from tastypie import fields
from tastypie.authentication import Authentication
from tastypie.resources import Resource, ModelResource, ALL, ALL_WITH_RELATIONS

from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import F, Sum

from aligulac.settings import DEBUG
from aligulac.tools import ntz

from ratings.inference_views import (
    DualPredictionResult,
    MatchPredictionResult,
    RoundRobinPredictionResult,
    SingleEliminationPredictionResult,
    ProleaguePredictionResult,
)
from ratings.models import (
    APIKey,
    Earnings,
    Event,
    Group,
    GroupMembership,
    Match,
    Period,
    Player,
    Rating,
    P, T, Z
)
from ratings.tools import (
    filter_active,
    total_ratings,
    count_winloss_player,
    count_matchup_player,
)

class APIKeyAuthentication(Authentication):
    def is_authenticated(self, request, **kwargs):
        if DEBUG:
            return True

        try:
            key = request.POST['apikey'] if request.method == 'POST' else request.GET['apikey']
        except:
            return False

        modified = APIKey.objects.filter(key=key).update(requests=F('requests')+1)
        return modified == 1

class PeriodResource(ModelResource):
    class Meta:
        queryset = Period.objects.filter(computed=True)
        allowed_methods = ['get', 'post']
        resource_name = 'period'
        authentication = APIKeyAuthentication()
        excludes = ['computed']
        filtering = {
            'id':               ALL,
            'start':            ALL,
            'end':              ALL,
            'needs_recompute':  ALL,
            'num_retplayers':   ALL,
            'num_games':        ALL,
            'dom_p':            ALL,
            'dom_t':            ALL,
            'dom_z':            ALL,
        }
        ordering = [
            'id', 'start', 'end', 'num_retplayers', 'num_newplayers', 'num_games', 'dom_p', 'dom_t', 'dom_z',
        ]

class SmallRatingResource(ModelResource):
    class Meta:
        queryset = total_ratings(Rating.objects.all())
        allowed_methods = ['get', 'post']
        resource_name = 'rating'
        authentication = APIKeyAuthentication()
        fields = [
            'id',
            'rating', 'rating_vp', 'rating_vt', 'rating_vz',
            'dev', 'dev_vp', 'dev_vt', 'dev_vz',
            'decay',
        ]
        filtering = {
            'id':         ALL,
            'period':     ALL_WITH_RELATIONS,
            'player':     ALL_WITH_RELATIONS,
            'prev':       ALL_WITH_RELATIONS,
            'decay':      ALL,
            'domination': ALL,
            'rating':     ALL, 'rating_vp':     ALL, 'rating_vt':     ALL, 'rating_vz':     ALL,
            'dev':        ALL, 'dev_vp':        ALL, 'dev_vt':        ALL, 'dev_vz':        ALL,
            'bf_rating':  ALL, 'bf_rating_vp':  ALL, 'bf_rating_vt':  ALL, 'bf_rating_vz':  ALL,
            'bf_dev':     ALL, 'bf_dev_vp':     ALL, 'bf_dev_vt':     ALL, 'bf_dev_vz':     ALL,
            'comp_rat':   ALL, 'comp_rat_vp':   ALL, 'comp_rat_vt':   ALL, 'comp_rat_vz':   ALL,
            'position':   ALL, 'position_vp':   ALL, 'position_vt':   ALL, 'position_vz':   ALL,
        }

    def dehydrate(self, bundle):
        bundle.data['tot_vp'] = bundle.data['rating'] + bundle.data['rating_vp']
        bundle.data['tot_vt'] = bundle.data['rating'] + bundle.data['rating_vt']
        bundle.data['tot_vz'] = bundle.data['rating'] + bundle.data['rating_vz']
        return bundle

class RatingResource(ModelResource):
    class Meta:
        queryset = total_ratings(Rating.objects.all())
        allowed_methods = ['get', 'post']
        resource_name = 'rating'
        authentication = APIKeyAuthentication()
        filtering = {
            'id':         ALL,
            'period':     ALL_WITH_RELATIONS,
            'player':     ALL_WITH_RELATIONS,
            'prev':       ALL_WITH_RELATIONS,
            'decay':      ALL,
            'domination': ALL,
            'rating':     ALL, 'rating_vp':     ALL, 'rating_vt':     ALL, 'rating_vz':     ALL,
            'dev':        ALL, 'dev_vp':        ALL, 'dev_vt':        ALL, 'dev_vz':        ALL,
            'bf_rating':  ALL, 'bf_rating_vp':  ALL, 'bf_rating_vt':  ALL, 'bf_rating_vz':  ALL,
            'bf_dev':     ALL, 'bf_dev_vp':     ALL, 'bf_dev_vt':     ALL, 'bf_dev_vz':     ALL,
            'comp_rat':   ALL, 'comp_rat_vp':   ALL, 'comp_rat_vt':   ALL, 'comp_rat_vz':   ALL,
            'position':   ALL, 'position_vp':   ALL, 'position_vt':   ALL, 'position_vz':   ALL,
        }
        ordering = [
            'id',
            'period',
            'player',
            'prev',
            'decay',
            'domination',
            'rating',     'rating_vp',     'rating_vt',     'rating_vz',
            'dev',        'dev_vp',        'dev_vt',        'dev_vz',
            'bf_rating',  'bf_rating_vp',  'bf_rating_vt',  'bf_rating_vz',
            'bf_dev',     'bf_dev_vp',     'bf_dev_vt',     'bf_dev_vz',
            'comp_rat',   'comp_rat_vp',   'comp_rat_vt',   'comp_rat_vz',
            'position',   'position_vp',   'position_vt',   'position_vz',
        ]

    def dehydrate(self, bundle):
        bundle.data['tot_vp'] = bundle.data['rating'] + bundle.data['rating_vp']
        bundle.data['tot_vt'] = bundle.data['rating'] + bundle.data['rating_vt']
        bundle.data['tot_vz'] = bundle.data['rating'] + bundle.data['rating_vz']
        return bundle

    period = fields.ForeignKey(PeriodResource, 'period', null=False)
    player = fields.ForeignKey('ratings.api.resources.SmallPlayerResource', 'player', null=False, full=True)
    prev = fields.ForeignKey('self', 'prev', null=True)

class ActiveRatingResource(ModelResource):
    class Meta:
        queryset = filter_active(total_ratings(Rating.objects.all()))
        allowed_methods = ['get', 'post']
        resource_name = 'activerating'
        authentication = APIKeyAuthentication()
        filtering = {
            'id':         ALL,
            'period':     ALL_WITH_RELATIONS,
            'player':     ALL_WITH_RELATIONS,
            'prev':       ALL_WITH_RELATIONS,
            'decay':      ALL,
            'domination': ALL,
            'rating':     ALL, 'rating_vp':     ALL, 'rating_vt':     ALL, 'rating_vz':     ALL,
            'dev':        ALL, 'dev_vp':        ALL, 'dev_vt':        ALL, 'dev_vz':        ALL,
            'bf_rating':  ALL, 'bf_rating_vp':  ALL, 'bf_rating_vt':  ALL, 'bf_rating_vz':  ALL,
            'bf_dev':     ALL, 'bf_dev_vp':     ALL, 'bf_dev_vt':     ALL, 'bf_dev_vz':     ALL,
            'comp_rat':   ALL, 'comp_rat_vp':   ALL, 'comp_rat_vt':   ALL, 'comp_rat_vz':   ALL,
            'position':   ALL, 'position_vp':   ALL, 'position_vt':   ALL, 'position_vz':   ALL,
        }
        ordering = [
            'id',
            'period',
            'player',
            'prev',
            'decay',
            'domination',
            'rating',     'rating_vp',     'rating_vt',     'rating_vz',
            'dev',        'dev_vp',        'dev_vt',        'dev_vz',
            'bf_rating',  'bf_rating_vp',  'bf_rating_vt',  'bf_rating_vz',
            'bf_dev',     'bf_dev_vp',     'bf_dev_vt',     'bf_dev_vz',
            'comp_rat',   'comp_rat_vp',   'comp_rat_vt',   'comp_rat_vz',
            'position',   'position_vp',   'position_vt',   'position_vz',
        ]

    def dehydrate(self, bundle):
        bundle.data['tot_vp'] = bundle.data['rating'] + bundle.data['rating_vp']
        bundle.data['tot_vt'] = bundle.data['rating'] + bundle.data['rating_vt']
        bundle.data['tot_vz'] = bundle.data['rating'] + bundle.data['rating_vz']
        return bundle

    period = fields.ForeignKey(PeriodResource, 'period', null=False)
    player = fields.ForeignKey('ratings.api.resources.SmallPlayerResource', 'player', null=False, full=True)
    prev = fields.ForeignKey('self', 'prev', null=True)

class SmallPlayerResource(ModelResource):
    class Meta:
        queryset = Player.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'player'
        authentication = APIKeyAuthentication()
        fields = ['id', 'tag', 'country', 'race']
        filtering = {
            'id':       ALL,
            'tag':      ALL,
            'country':  ALL,
            'race':     ALL
        }

class PlayerResource(ModelResource):
    class Meta:
        queryset = Player.objects.all().prefetch_related('alias_set')
        allowed_methods = ['get', 'post']
        resource_name = 'player'
        authentication = APIKeyAuthentication()
        filtering = {
            'id':              ALL,
            'tag':             ALL,
            'name':            ALL,
            'birthday':        ALL,
            'mcnum':           ALL,
            'tlpd_id':         ALL,
            'tlpd_db':         ALL,
            'lp_name':         ALL,
            'sc2e_id':         ALL,
            'country':         ALL,
            'race':            ALL,
            'dom_val':         ALL,
            'current_rating':  ALL_WITH_RELATIONS,
            'dom_start':       ALL_WITH_RELATIONS,
            'dom_end':         ALL_WITH_RELATIONS,
        }
        ordering = [
            'id', 'tag', 'name', 'birthday', 'mcnum', 'tlpd_id', 'tlpd_db', 'lp_name', 'sc2e_id', 'country',
            'race', 'dom_val', 'current_rating', 'dom_start', 'dom_end',
        ]

    def dehydrate_total_earnings(self, bundle):
        return ntz(bundle.obj.earnings_set.aggregate(Sum('earnings'))['earnings__sum'])

    def dehydrate_aliases(self, bundle):
        return [a.name for a in bundle.obj.alias_set.all()]

    def dehydrate_form(self, bundle):
        matches = bundle.obj.get_matchset()
        recent = matches.filter(date__gte=(date.today() - relativedelta(months=2)))
        return {'total': count_winloss_player(recent, bundle.obj),
                'P': count_matchup_player(recent, bundle.obj, P),
                'T': count_matchup_player(recent, bundle.obj, T),
                'Z': count_matchup_player(recent, bundle.obj, Z)}

    dom_start = fields.ForeignKey(PeriodResource, 'dom_start', blank=True, null=True)
    dom_end = fields.ForeignKey(PeriodResource, 'dom_end', blank=True, null=True)
    current_rating = fields.ForeignKey(SmallRatingResource, 'current_rating', blank=True, null=True, full=True)

    current_teams = fields.ToManyField(
        'ratings.api.resources.SmallGroupMembershipResourceFromPlayer', null=True, full=True,
        attribute=lambda b: b.obj.groupmembership_set.filter(current=True, group__is_team=True),
        help_text='Current team(s)'
    )
    past_teams = fields.ToManyField(
        'ratings.api.resources.SmallGroupMembershipResourceFromPlayer', null=True, full=True,
        attribute=lambda b: b.obj.groupmembership_set.filter(current=False, group__is_team=True),
        help_text='Past teams'
    )

    total_earnings = fields.FloatField(help_text='Total earnings (USD)')

    form = fields.DictField(help_text='Recent form (last two months)')

    aliases = fields.ListField(null=True, help_text='Aliases')

class SmallEventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'event'
        authentication = APIKeyAuthentication()
        fields = ['id', 'fullname']
        filtering = {
            'id':         ALL,
            'name':       ALL,
            'fullname':   ALL,
            'parent':     ALL_WITH_RELATIONS,
            'homepage':   ALL,
            'lp_name':    ALL,
            'tlpd_id':    ALL,
            'tlpd_db':    ALL,
            'tl_thread':  ALL,
            'prizepool':  ALL,
            'earliest':   ALL,
            'latest':     ALL,
            'category':   ALL,
            'type':       ALL,
        }

class EventResource(ModelResource):
    class Meta:
        queryset = Event.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'event'
        authentication = APIKeyAuthentication()
        excludes = ['lft', 'rgt', 'closed', 'big', 'noprint']
        filtering = {
            'id':         ALL,
            'name':       ALL,
            'fullname':   ALL,
            'parent':     ALL_WITH_RELATIONS,
            'homepage':   ALL,
            'lp_name':    ALL,
            'tlpd_id':    ALL,
            'tlpd_db':    ALL,
            'tl_thread':  ALL,
            'prizepool':  ALL,
            'earliest':   ALL,
            'latest':     ALL,
            'category':   ALL,
            'type':       ALL,
            'idx':        ALL,
        }
        ordering = ['id', 'earliest', 'latest', 'idx']

    parent = fields.ForeignKey('self', 'parent', null=True)
    children = fields.ToManyField(
        'self', attribute=lambda b: Event.objects.filter(uplink__parent=b.obj, uplink__distance=1),
        null=True, help_text='Direct children events'
    )
    earnings = fields.ToManyField(
        'ratings.api.resources.EarningResource', attribute=lambda b: b.obj.earnings_set,
        null=True, help_text='Prizes awarded'
    )

    def build_filters(self, filters=None):
        check = ['uplink__parent', 'uplink__distance', 'downlink__child', 'downlink__distance']
        fits = lambda s: any(filter(lambda k: s.startswith(k), check))
        other_filters = {f: filters[f] for f in filters if not fits(f)}
        orm_filters = super(EventResource, self).build_filters(other_filters)
        for f in filter(fits, filters):
            is_pure = f in check
            if is_pure or any(filter(lambda s: f.endswith(s), ['gt', 'gte', 'lt', 'lte'])):
                orm_filters[f] = filters[f]
            elif any(filter(lambda s: f.endswith(s), ['in', 'range'])):
                orm_filters[f] = filters[f].split(',')
        return orm_filters

class MatchResource(ModelResource):
    class Meta:
        queryset = Match.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'match'
        authentication = APIKeyAuthentication()
        filtering = {
            'id':        ALL,
            'period':    ALL_WITH_RELATIONS,
            'eventobj':  ALL_WITH_RELATIONS,
            'rta':       ALL_WITH_RELATIONS,
            'rtb':       ALL_WITH_RELATIONS,
            'pla':       ALL_WITH_RELATIONS,
            'plb':       ALL_WITH_RELATIONS,
            'sca':       ALL,
            'scb':       ALL,
            'rca':       ALL,
            'rcb':       ALL,
            'date':      ALL,
            'treated':   ALL,
            'event':     ALL,
            'game':      ALL,
            'offline':   ALL,
        }
        ordering = [
            'id', 'period', 'eventobj', 'rta', 'rtb', 'pla', 'plb', 'sca', 'scb', 'rca', 'rcb',
            'date', 'treated', 'event', 'game', 'offline',
        ]

    pla = fields.ForeignKey(SmallPlayerResource, 'pla', null=False, full=True)
    plb = fields.ForeignKey(SmallPlayerResource, 'plb', null=False, full=True)
    rta = fields.ForeignKey(SmallRatingResource, 'rta', null=True, full=True)
    rtb = fields.ForeignKey(SmallRatingResource, 'rtb', null=True, full=True)
    eventobj = fields.ForeignKey(SmallEventResource, 'eventobj', null=True, full=True)

    def build_filters(self, filters=None):
        check = [
            'eventobj__uplink__parent',
            'eventobj__uplink__distance',
            'eventobj__downlink__child',
            'eventobj__downlink__distance',
        ]
        fits = lambda s: any(filter(lambda k: s.startswith(k), check))
        other_filters = {f: filters[f] for f in filters if not fits(f)}
        orm_filters = super(MatchResource, self).build_filters(other_filters)
        for f in filter(fits, filters):
            is_pure = f in check
            if is_pure or any(filter(lambda s: f.endswith(s), ['gt', 'gte', 'lt', 'lte'])):
                orm_filters[f] = filters[f]
            elif any(filter(lambda s: f.endswith(s), ['in', 'range'])):
                orm_filters[f] = filters[f].split(',')
        return orm_filters

class EarningResource(ModelResource):
    class Meta:
        queryset = Earnings.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'earning'
        authentication = APIKeyAuthentication()
        filtering = {
            'id':            ALL,
            'event':         ALL_WITH_RELATIONS,
            'player':        ALL_WITH_RELATIONS,
            'earnings':      ALL,
            'origearnings':  ALL,
            'currency':      ALL,
            'placement':     ALL,
        }
        ordering = ['id', 'event', 'player', 'earnings', 'origearnings', 'currency', 'placement']

    event = fields.ForeignKey(SmallEventResource, 'event', null=False, full=True)
    player = fields.ForeignKey(SmallPlayerResource, 'player', null=False, full=True)

class SmallGroupMembershipResourceFromPlayer(ModelResource):
    class Meta:
        queryset = GroupMembership.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'groupmembership'
        authentication = APIKeyAuthentication()
        excludes = ['current']

    team = fields.ForeignKey('ratings.api.resources.SmallTeamResource', 'group', full=True)

class SmallGroupMembershipResourceFromGroup(ModelResource):
    class Meta:
        queryset = GroupMembership.objects.all()
        allowed_methods = ['get', 'post']
        resource_name = 'groupmembership'
        authentication = APIKeyAuthentication()
        excludes = ['current', 'playing']

    player = fields.ForeignKey(SmallPlayerResource, 'player', full=True)

class SmallTeamResource(ModelResource):
    class Meta:
        queryset = Group.objects.filter(is_team=True)
        allowed_methods = ['get', 'post']
        resource_name = 'team'
        authentication = APIKeyAuthentication()
        fields = ['name', 'shortname', 'id']
        filtering = {
            'id': ALL,
            'name': ALL,
            'shortname': ALL,
            'scoreak': ALL,
            'scorepl': ALL,
            'meanrating': ALL,
            'founded': ALL,
            'disbanded': ALL,
            'active': ALL,
            'homepage': ALL,
            'lp_name': ALL,
        }

class TeamResource(ModelResource):
    class Meta:
        queryset = Group.objects.filter(is_team=True).prefetch_related('alias_set')
        allowed_methods = ['get', 'post']
        resource_name = 'team'
        authentication = APIKeyAuthentication()
        excludes = ['is_team', 'is_manual']
        filtering = {
            'id': ALL,
            'name': ALL,
            'shortname': ALL,
            'scoreak': ALL,
            'scorepl': ALL,
            'meanrating': ALL,
            'founded': ALL,
            'disbanded': ALL,
            'active': ALL,
            'homepage': ALL,
            'lp_name': ALL,
        }
        ordering = [
            'id', 'name', 'shortname', 'scoreak', 'scorepl', 'meanrating', 'founded', 'disbanded', 'active',
            'homepage', 'lp_name',
        ]

    def dehydrate_aliases(self, bundle):
        return [a.name for a in bundle.obj.alias_set.all()]

    current_players = fields.ToManyField(
        SmallGroupMembershipResourceFromGroup, null=True, full=True,
        attribute=lambda b: b.obj.groupmembership_set.filter(current=True, playing=True),
        help_text='Currently affiliated players'
    )
    current_nonplayers = fields.ToManyField(
        SmallGroupMembershipResourceFromGroup, null=True, full=True,
        attribute=lambda b: b.obj.groupmembership_set.filter(current=True, playing=False),
        help_text='Currently affiliated non-players'
    )
    past_players = fields.ToManyField(
        SmallGroupMembershipResourceFromGroup, null=True, full=True,
        attribute=lambda b: b.obj.groupmembership_set.filter(current=False),
        help_text='Past players'
    )

    aliases = fields.ListField(null=True, help_text='Aliases')

class PredictResource(Resource):
    def get_resource_uri(self, bundle_or_obj):
        kwargs = {'resource_name': self._meta.resource_name}

        # Fill in kwargs['pk'] here by referencing bundle_or_obj.obj or bundle_or_obj
        kwargs['pk'] = ','.join([str(p.id) if p else '-1' for p in bundle_or_obj.obj.dbpl])

        if self._meta.api_name is not None:
            kwargs['api_name'] = self._meta.api_name

        s = unquote(self._build_reverse_url('api_dispatch_detail', kwargs=kwargs))
        s += '?bo=%s' % ','.join([str(2*b-1) for b in bundle_or_obj.obj.bos])
        q = bundle_or_obj.obj.generate_updates()
        if q:
            s += '&' + q
        return s

    def get_object_list(self, request):
        pass

    def clean_pk(self, pk):
        player_ids = [int(a) for a in pk.split(',')]
        players = Player.objects.in_bulk(player_ids)
        return [players[id] if id in players else None for id in player_ids]

    def get_detail(self, request, **kwargs):
        basic_bundle = self.build_bundle(request=request)

        try:
            obj = self.cached_obj_get(
                bundle=basic_bundle,
                request=request,
                **self.remove_api_resource_names(kwargs)
            )
        except ObjectDoesNotExist:
            return http.HttpNotFound()
        except MultipleObjectsReturned:
            return http.HttpMultipleChoices("More than one resource is found at this URI.")

        bundle = self.build_bundle(obj=obj, request=request)
        bundle = self.full_dehydrate(bundle)
        bundle = self.alter_detail_data_to_serialize(request, bundle)
        return self.create_response(request, bundle)

class PredictCombinationResource(PredictResource):
    def dehydrate_matches(self, bundle):
        for m in bundle.data['matches']:
            del m['match_id']
            del m['sim']
        return bundle.data['matches']

    def dehydrate_meanres(self, bundle):
        for m in bundle.data['meanres']:
            del m['match_id']
        return bundle.data['meanres']

    def obj_get(self, request=None, **kwargs):
        args = request.GET if request.method == 'GET' else request.POST

        return self.Meta.object_class(
            dbpl=self.clean_pk(kwargs['pk']),
            bos=[(int(b)+1)//2 for b in args['bo'].split(',')],
            args=args,
        )

    matches = fields.ListField('matches', null=False, help_text='Matches')
    meanres = fields.ListField('meanres', null=False, help_text='Median results')

class PredictMatchResource(PredictResource):
    class Meta:
        allowed_methods = ['get', 'post']
        resource_name = 'predictmatch'
        authentication = APIKeyAuthentication()
        object_class = MatchPredictionResult

    pla = fields.ForeignKey(SmallPlayerResource, 'pla', null=False, help_text='Player A', full=True)
    plb = fields.ForeignKey(SmallPlayerResource, 'plb', null=False, help_text='Player B', full=True)
    sca = fields.IntegerField('sca', null=False, help_text='Predefined score for player A')
    scb = fields.IntegerField('scb', null=False, help_text='Predefined score for player B')
    proba = fields.FloatField('proba', null=False, help_text='Probability of winning for player A')
    probb = fields.FloatField('probb', null=False, help_text='Probability of winning for player B')
    rta = fields.FloatField('rta', null=False, help_text='Rating for player A vs. player B')
    rtb = fields.FloatField('rtb', null=False, help_text='Rating for player B vs. player A')
    outcomes = fields.ListField('outcomes', null=True, help_text='Detailed outcomes')

    def obj_get(self, request=None, **kwargs):
        args = request.GET if request.method == 'GET' else request.POST

        return MatchPredictionResult(
            dbpl=self.clean_pk(kwargs['pk']),
            bos=[(int(b)+1)//2 for b in args['bo'].split(',')],
            s1=args.get('s1', 0),
            s2=args.get('s2', 0),
        )

class PredictDualResource(PredictCombinationResource):
    class Meta:
        allowed_methods = ['get', 'post']
        resource_name = 'predictdual'
        authentication = APIKeyAuthentication()
        object_class = DualPredictionResult

    table = fields.ListField('table', null=False, help_text='Predicted table')

class PredictSEBracketResource(PredictCombinationResource):
    class Meta:
        allowed_methods = ['get', 'post']
        resource_name = 'predictsebracket'
        authentication = APIKeyAuthentication()
        object_class = SingleEliminationPredictionResult

    table = fields.ListField('table', null=False, help_text='Predicted table')

class PredictRRGroupResource(PredictCombinationResource):
    class Meta:
        allowed_methods = ['get', 'post']
        resource_name = 'predictrrgroup'
        authentication = APIKeyAuthentication()
        object_class = RoundRobinPredictionResult

    table = fields.ListField('table', null=False, help_text='Predicted table')
    mtable = fields.ListField('mtable', null=False, help_text='Median table')

class PredictPLResource(PredictCombinationResource):
    class Meta:
        allowed_methods = ['get', 'post']
        resource_name = 'predictproleague'
        authentication = APIKeyAuthentication()
        object_class = ProleaguePredictionResult

    outcomes = fields.ListField('outcomes', null=False, help_text='Possible outcomes')
    proba = fields.FloatField('proba', null=False, help_text='Probability for Team A winning')
    probb = fields.FloatField('probb', null=False, help_text='Probability for Team B winning')
    prob_draw = fields.FloatField('prob_draw', null=False, help_text='Probability for a draw')
    sca = fields.IntegerField('s1', null=False, help_text='Predefined score for Team A')
    scb = fields.IntegerField('s2', null=False, help_text='Predefined score for Team B')
