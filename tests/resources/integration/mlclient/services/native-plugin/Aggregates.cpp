#include <MarkLogic.h>

using namespace marklogic;

enum Result { NUMBER, TEXT, MAP, EMPTY };

template<Result result>
class TestAggregate : public AggregateUDF {
    double sum = 0;
    uint64_t count = 0;
public:
    AggregateUDF* clone() const { return new TestAggregate(*this); }
    void close() { delete this; }
    void start(Sequence&, Reporter&) {}
    void map(TupleIterator& values, Reporter&) {
        for (; !values.done(); values.next()) {
            if (values.null(0)) continue;
            double value;
            values.value(0, value);
            sum += value * values.frequency();
            count += values.frequency();
        }
    }
    void reduce(const AggregateUDF* other, Reporter&) {
        const TestAggregate* aggregate = static_cast<const TestAggregate*>(other);
        sum += aggregate->sum;
        count += aggregate->count;
    }
    void encode(Encoder& encoder, Reporter&) {
        encoder.encode(sum);
        encoder.encode(count);
    }
    void decode(Decoder& decoder, Reporter&) {
        decoder.decode(sum);
        decoder.decode(count);
    }
    void finish(OutputSequence& output, Reporter&) {
        if (!count || result == EMPTY) return;
        if (result == NUMBER) output.writeValue(sum / count);
        if (result == TEXT) output.writeValue(String("native aggregate"));
        if (result == MAP) {
            output.startMap();
            output.writeMapKey("mean");
            output.writeValue(sum / count);
            output.endMap();
        }
    }
};

extern "C" void marklogicPlugin(Registry& registry) {
    registry.version();
    registry.registerAggregate<TestAggregate<NUMBER> >("mean");
    registry.registerAggregate<TestAggregate<TEXT> >("label");
    registry.registerAggregate<TestAggregate<MAP> >("summary");
    registry.registerAggregate<TestAggregate<EMPTY> >("empty");
}
